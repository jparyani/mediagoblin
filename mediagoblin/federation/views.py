import json

from mediagoblin.decorators import oauth_required
from mediagoblin.db.models import User, MediaEntry, MediaComment
from mediagoblin.tools.response import redirect, json_response
from mediagoblin.meddleware.csrf import csrf_exempt

#@oauth_required
def profile(request, raw=False):
    """ This is /api/user/<username>/profile - This will give profile info """
    user = request.matchdict["username"]
    requested_user = User.query.filter_by(username=user)
    
    # check if the user exists
    if requested_user is None:
        error = "No such 'user' with id '{0}'".format(user)
        return json_response({"error": error}, status=404)

    user = requested_user[0]

    if raw:
        return (user, user.serialize(request))

    # user profiles are public so return information
    return json_response(user.serialize(request))

def user(request):
    """ This is /api/user/<username> - This will get the user """
    user, user_profile = profile(request, raw=True)
    data = {
        "nickname": user.username,
        "updated": user.created.isoformat(),
        "published": user.created.isoformat(),
        "profile": user_profile
        }

    return json_response(data)

@oauth_required
@csrf_exempt
def feed(request):
    """ Handles the user's outbox - /api/user/<username>/feed """
    print request.user
    user = request.matchdict["username"]
    requested_user = User.query.filter_by(username=user)

    # check if the user exists
    if requested_user is None:
        error = "No such 'user' with id '{0}'".format(user)
        return json_response({"error": error}, status=404)

    user = requested_user[0]

    if request.method == "POST":
        data = json.loads(request.data)
        obj = data.get("object", None)
        if obj is None:
            error = {"error": "Could not find 'object' element."}
            return json_response(error, status=400)
  
        if obj.get("objectType", None) == "comment":
            # post a comment
            media = int(data["object"]["inReplyTo"]["id"])
            author = request.user
            comment = MediaComment(
                media_entry=media,
                author=request.user.id,
                content=data["object"]["content"]
                )
            comment.save()
        elif obj.get("objectType", None) is None:
            error = {"error": "No objectType specified."}
            return json_response(error, status=400)
        else:
            error = {"error": "Unknown object type '{0}'.".format(obj.get("objectType", None))}
            return json_response(error, status=400)

    feed_url = request.urlgen(
            "mediagoblin.federation.feed",
            username=user.username,
            qualified=True
            )

    feed = {
        "displayName": "Activities by {0}@{1}".format(user.username, request.host),
        "objectTypes": ["activity"],
        "url": feed_url,
        "links": {
            "first": {
                "href": feed_url,
            },
            "self": {
                "href": request.url,
            },
            "prev": {
                "href": feed_url,
            },
            "next": {
                "href": feed_url,
            }
        },
        "author": user.serialize(request),
        "items": [],
    }
    

    # Now lookup the user's feed.
    for media in MediaEntry.query.all():
        feed["items"].append({
            "verb": "post",
            "object": media.serialize(request),
            "actor": user.serialize(request),
            "content": "{0} posted a picture".format(user.username),
            "id": 1,
            })
        feed["items"][-1]["updated"] = feed["items"][-1]["object"]["updated"]
        feed["items"][-1]["published"] = feed["items"][-1]["object"]["published"]
        feed["items"][-1]["url"] = feed["items"][-1]["object"]["url"]
    feed["totalItems"] = len(feed["items"])

    return json_response(feed)

@oauth_required
def inbox(request):
    """ Handles the user's inbox - /api/user/<username>/inbox """
    raise NotImplemented("Yet to implement looking up user's inbox")

#@oauth_required
def object(request, raw_obj=False):
    """ Lookup for a object type """
    objectType = request.matchdict["objectType"]
    uuid = request.matchdict["uuid"]
    if objectType not in ["image"]:
        error = "Unknown type: {0}".format(objectType)
        # not sure why this is 404, maybe ask evan. Maybe 400? 
        return json_response({"error": error}, status=404)

    media = MediaEntry.query.filter_by(slug=uuid).first()
    if media is None:
        # no media found with that uuid
        error = "Can't find a {0} with ID = {1}".format(objectType, uuid)
        return json_response({"error": error}, status=404)

    if raw_obj:
        return media

    return json_response(media.serialize(request))

def object_comments(request):
    """ Looks up for the comments on a object """
    media = object(request, raw_obj=True)
    response = media
    if isinstance(response, MediaEntry):
        comments = response.serialize(request)
        comments = comments.get("replies", {
                "totalItems": 0,
                "items": [],
                "url": request.urlgen(
                    "mediagoblin.federation.object.comments",
                    objectType=media.objectType,
                    uuid=media.slug,
                    qualified=True)
                })
        comments["displayName"] = "Replies to {0}".format(comments["url"])
        comments["links"] = {
            "first": comments["url"],
            "self": comments["url"],
        }
        response = json_response(comments)

    return response


##
# Well known
##
def host_meta(request):
    """ This is /.well-known/host-meta - provides URL's to resources on server """
    links = []
    
    # Client registration links
    links.append({
        "ref": "registration_endpoint",
        "href": request.urlgen("mediagoblin.oauth.client_register", qualified=True),
        })
    links.append({
        "ref": "http://apinamespace.org/oauth/request_token",
        "href": request.urlgen("mediagoblin.oauth.request_token", qualified=True),
        })
    links.append({
        "ref": "http://apinamespace.org/oauth/authorize",
        "href": request.urlgen("mediagoblin.oauth.authorize", qualified=True),
        })
    links.append({
        "ref": "http://apinamespace.org/oauth/access_token",
        "href": request.urlgen("mediagoblin.oauth.access_token", qualified=True),
        })

    return json_response({"links": links})

def whoami(request):
    """ This is /api/whoami - This is a HTTP redirect to api profile """
    profile = request.urlgen(
        "mediagoblin.federation.user.profile",
        username=request.user.username,
        qualified=True
        )

    return redirect(request, location=profile)
