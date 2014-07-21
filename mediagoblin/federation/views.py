# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import io
import mimetypes

from werkzeug.datastructures import FileStorage

from mediagoblin.media_types import sniff_media
from mediagoblin.decorators import oauth_required
from mediagoblin.federation.decorators import user_has_privilege
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
        "profile": user_profile,
    }

    return json_response(data)

@oauth_required
@csrf_exempt
@user_has_privilege(u'uploader')
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
        if "Content-Type" not in request.headers:
            error = "Must supply 'Content-Type' header to upload media."
            return json_response({"error": error}, status=400)
        mimetype = request.headers["Content-Type"]
        filename = mimetypes.guess_all_extensions(mimetype)
        filename = 'unknown' + filename[0] if filename else filename
        file_data = FileStorage(
            stream=io.BytesIO(request.data),
            filename=filename,
            content_type=mimetype
        )

        # Find media manager
        media_type, media_manager = sniff_media(file_data, filename)
        entry = new_upload_entry(request.user)
        if hasattr(media_manager, "api_upload_request"):
            return media_manager.api_upload_request(request, file_data, entry)
        else:
            return json_response({"error": "Not yet implemented"}, status=501)

    return json_response({"error": "Not yet implemented"}, status=501)

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
    if request.data:
        data = json.loads(request.data)
    else:
        data = {"verb": None, "object": {}}

    if request.method == "POST" and data["verb"] == "post":
        obj = data.get("object", None)
        if obj is None:
            error = {"error": "Could not find 'object' element."}
            return json_response(error, status=400)

        if obj.get("objectType", None) == "comment":
            # post a comment
            comment = MediaComment(author=request.user.id)
            comment.unserialize(data["object"])
            comment.save()
            data = {"verb": "post", "object": comment.serialize(request)}
            return json_response(data)

        elif obj.get("objectType", None) == "image":
            # Posting an image to the feed
            media_id = int(data["object"]["id"])
            media = MediaEntry.query.filter_by(id=media_id)
            if media is None:
                error = "No such 'image' with id '{0}'".format(id=media_id)
                return json_response(error, status=404)

            media = media.first()
            if not media.unserialize(data["object"]):
                error = "Invalid 'image' with id '{0}'".format(media_id)
                return json_response({"error": error}, status=400)
            media.save()
            media.media_manager.api_add_to_feed(request, media)

            return json_response({
                "verb": "post",
                "object": media.serialize(request)
            })

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

    elif request.method in ["PUT", "POST"] and data["verb"] == "update":
        # Check we've got a valid object
        obj = data.get("object", None)

        if obj is None:
            error = {"error": "Could not find 'object' element."}
            return json_response(error, status=400)

        if "objectType" not in obj:
            error = {"error": "No objectType specified."}
            return json_response(error, status=400)

        if "id" not in obj:
            error = {"error": "Object ID has not been specified."}
            return json_response(error, status=400)

        obj_id = obj["id"]

        # Now try and find object
        if obj["objectType"] == "comment":
            comment = MediaComment.query.filter_by(id=obj_id)
            if comment is None:
                error = "No such 'comment' with id '{0}'.".format(obj_id)
                return json_response({"error": error}, status=400)

            comment = comment[0]
            if not comment.unserialize(data["object"]):
                error = "Invalid 'comment' with id '{0}'".format(obj_id)
                return json_response({"error": error}, status=400)

            comment.save()

            activity = {
                "verb": "update",
                "object": comment.serialize(request),
            }
            return json_response(activity)

        elif obj["objectType"] == "image":
            image = MediaEntry.query.filter_by(id=obj_id)
            if image is None:
                error = "No such 'image' with the id '{0}'.".format(obj_id)
                return json_response({"error": error}, status=400)

            image = image[0]
            if not image.unserialize(obj):
                "Invalid 'image' with id '{0}'".format(obj_id)
                return json_response({"error": error}, status=400)
            image.save()

            activity = {
                "verb": "update",
                "object": image.serialize(request),
            }
            return json_response(activity)

    elif request.method != "GET":
        # Currently unsupported
        error = "Unsupported HTTP method {0}".format(request.method)
        return json_response({"error": error}, status=501)

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
        item = {
            "verb": "post",
            "object": media.serialize(request),
            "actor": request.user.serialize(request),
            "content": "{0} posted a picture".format(request.user.username),
            "id": 1,
        }
        item["updated"] = item["object"]["updated"]
        item["published"] = item["object"]["published"]
        item["url"] = item["object"]["url"]
        feed["items"].append(item)
    feed["totalItems"] = len(feed["items"])

    return json_response(feed)

@oauth_required
def object(request, raw_obj=False):
    """ Lookup for a object type """
    object_type = request.matchdict["objectType"]
    try:
        object_id = int(request.matchdict["id"])
    except ValueError:
        error = "Invalid object ID '{0}' for '{1}'".format(
            request.matchdict["id"],
            object_type
        )
        return json_response({"error": error}, status=400)

    if object_type not in ["image"]:
        error = "Unknown type: {0}".format(object_type)
        # not sure why this is 404, maybe ask evan. Maybe 400?
        return json_response({"error": error}, status=404)

    media = MediaEntry.query.filter_by(id=object_id).first()
    if media is None:
        # no media found with that uuid
        error = "Can't find '{0}' with ID '{1}'".format(
            object_type,
            object_id
        )
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
                uuid=media.id,
                qualified=True
            )
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
    """ /.well-known/host-meta - provide URLs to resources """
    links = []

    links.append({
        "ref": "registration_endpoint",
        "href": request.urlgen(
            "mediagoblin.oauth.client_register",
            qualified=True
        ),
    })
    links.append({
        "ref": "http://apinamespace.org/oauth/request_token",
        "href": request.urlgen(
            "mediagoblin.oauth.request_token",
            qualified=True
        ),
    })
    links.append({
        "ref": "http://apinamespace.org/oauth/authorize",
        "href": request.urlgen(
            "mediagoblin.oauth.authorize",
            qualified=True
        ),
    })
    links.append({
        "ref": "http://apinamespace.org/oauth/access_token",
        "href": request.urlgen(
            "mediagoblin.oauth.access_token",
            qualified=True
        ),
    })

    return json_response({"links": links})

def whoami(request):
    """ /api/whoami - HTTP redirect to API profile """
    profile = request.urlgen(
        "mediagoblin.federation.user.profile",
        username=request.user.username,
        qualified=True
    )

    return redirect(request, location=profile)
