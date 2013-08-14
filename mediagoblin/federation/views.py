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

def image_object(request, media):
    """ Return image object - /api/image/<uuid> """
    author = media.get_uploader
    url = request.urlgen(
        "mediagoblin.user_pages.media_home",
        user=author.username,
        media=media.slug,
        qualified=True
        )

    context = {
        "author": author.serialize(request),
        "displayName": media.title,
        "objectType": "image",
        "url": url,
    }

    return json_response(context)

@oauth_required
def object(request):
    """ Lookup for a object type """
    objectType = request.matchdict["objectType"]
    uuid = request.matchdict["uuid"]
    if objectType not in ["image"]:
        error = "Unknown type: {0}".format(objectType)
        # not sure why this is 404, maybe ask evan. Maybe 400? 
        return json_response({"error": error}, status=404)

    media = MediaEntry.query.filter_by(uuid=uuid).first()
    if media is None:
        # no media found with that uuid
        error = "Can't find a {0} with ID = {1}".format(objectType, uuid)
        return json_response({"error": error}, status=404)

    if objectType == "image":
        return image_object(request, media)
