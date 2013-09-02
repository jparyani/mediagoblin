from mediagoblin.decorators import oauth_required
from mediagoblin.db.models import User, MediaEntry
from mediagoblin.tools.response import json_response

@oauth_required
def user(request):
    """ Handles user response at /api/user/<username>/ """
    user = request.matchdict["username"]
    requested_user = User.query.filter_by(username=user)
    
    # check if the user exists
    if requested_user is None:
        error = "No such 'user' with id '{0}'".format(user)
        return json_response({"error": error}, status=404)

    user = requested_user[0]

    # user profiles are public so return information
    return json_response(user.serialize(request))

@oauth_required
def feed(request):
    """ Handles the user's outbox - /api/user/<username>/feed """
    user = request.matchdict["username"]
    requested_user = User.query.filter_by(username=user)

    # check if the user exists
    if requested_user is None:
        error = "No such 'user' with id '{0}'".format(user)
        return json_response({"error": error}, status=404)

    user = request_user[0]

    # Now lookup the user's feed.
    raise NotImplemented("Yet to implement looking up user's feed")

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
        response = json_response(comments)

    return response
