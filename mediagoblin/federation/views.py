import json
import io
import mimetypes

from werkzeug.datastructures import FileStorage

from mediagoblin.media_types import sniff_media
from mediagoblin.decorators import oauth_required
from mediagoblin.db.models import User, MediaEntry, MediaComment
from mediagoblin.tools.response import redirect, json_response
from mediagoblin.meddleware.csrf import csrf_exempt
from mediagoblin.submit.lib import new_upload_entry

@oauth_required
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

@oauth_required
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
def uploads(request):
    """ Endpoint for file uploads """
    user = request.matchdict["username"]
    requested_user = User.query.filter_by(username=user)

    if requested_user is None:
        error = "No such 'user' with id '{0}'".format(user)
        return json_response({"error": error}, status=404)

    request.user = requested_user[0]
    if request.method == "POST":
        # Wrap the data in the werkzeug file wrapper
        mimetype = request.headers.get("Content-Type", "application/octal-stream")
        filename = mimetypes.guess_all_extensions(mimetype)
        filename = 'unknown' + filename[0] if filename else filename
        file_data = FileStorage(
            stream=io.BytesIO(request.data),
            filename=filename,
            content_type=request.headers.get("Content-Type", "application/octal-stream")
        )

        # Find media manager
        media_type, media_manager = sniff_media(file_data, filename)
        entry = new_upload_entry(request.user)
        if hasattr(media_manager, "api_upload_request"):
            return media_manager.api_upload_request(request, file_data, entry)
        else:
            return json_response({"error": "Not yet implemented"}, status=400)

    return json_response({"error": "Not yet implemented"}, status=400)

@oauth_required
@csrf_exempt
def feed(request):
    """ Handles the user's outbox - /api/user/<username>/feed """
    user = request.matchdict["username"]
    requested_user = User.query.filter_by(username=user)

    # check if the user exists
    if requested_user is None:
        error = "No such 'user' with id '{0}'".format(user)
        return json_response({"error": error}, status=404)

    request.user = requested_user[0]

    if request.method == "POST":
        data = json.loads(request.data)
        obj = data.get("object", None)
        if obj is None:
            error = {"error": "Could not find 'object' element."}
            return json_response(error, status=400)

        if obj.get("objectType", None) == "comment":
            # post a comment
            media = int(data["object"]["inReplyTo"]["id"])
            comment = MediaComment(
                media_entry=media,
                author=request.user.id,
                content=data["object"]["content"]
                )
            comment.save()
            data = {"verb": "post", "object": comment.serialize(request)}
            return json_response(data)

        elif obj.get("objectType", None) == "image":
            # Posting an image to the feed
            # NB: This is currently just handing the image back until we have an
            #     to send the image to the actual feed

            media_id = int(data["object"]["id"])
            media = MediaEntry.query.filter_by(id=media_id)
            if media is None:
                error = "No such 'image' with id '{0}'".format(id=media_id)
                return json_response(error, status=404)
            media = media[0]
            return json_response(media.serialize(request))

        elif obj.get("objectType", None) is None:
            # They need to tell us what type of object they're giving us.
            error = {"error": "No objectType specified."}
            return json_response(error, status=400)
        else:
            # Oh no! We don't know about this type of object (yet)
            error_message = "Unknown object type '{0}'.".format(
                obj.get("objectType", None)
            )

            error = {"error": error_message}
            return json_response(error, status=400)


    feed_url = request.urlgen(
            "mediagoblin.federation.feed",
            username=request.user.username,
            qualified=True
            )

    feed = {
        "displayName": "Activities by {user}@{host}".format(
            user=request.user.username,
            host=request.host
        ),
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
        "author": request.user.serialize(request),
        "items": [],
    }


    # Now lookup the user's feed.
    for media in MediaEntry.query.all():
        feed["items"].append({
            "verb": "post",
            "object": media.serialize(request),
            "actor": request.user.serialize(request),
            "content": "{0} posted a picture".format(request.user.username),
            "id": 1,
            })
        feed["items"][-1]["updated"] = feed["items"][-1]["object"]["updated"]
        feed["items"][-1]["published"] = feed["items"][-1]["object"]["published"]
        feed["items"][-1]["url"] = feed["items"][-1]["object"]["url"]
    feed["totalItems"] = len(feed["items"])

    return json_response(feed)

@oauth_required
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

@oauth_required
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
