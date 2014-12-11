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

from mediagoblin.decorators import oauth_required, require_active_login
from mediagoblin.federation.decorators import user_has_privilege
from mediagoblin.db.models import User, MediaEntry, MediaComment, Activity
from mediagoblin.tools.federation import create_activity, create_generator
from mediagoblin.tools.routing import extract_url_arguments
from mediagoblin.tools.response import redirect, json_response, json_error, \
                                       render_404, render_to_response
from mediagoblin.meddleware.csrf import csrf_exempt
from mediagoblin.submit.lib import new_upload_entry, api_upload_request, \
                                    api_add_to_feed

# MediaTypes
from mediagoblin.media_types.image import MEDIA_TYPE as IMAGE_MEDIA_TYPE

# Getters
def get_profile(request):
    """
    Gets the user's profile for the endpoint requested.

    For example an endpoint which is /api/{username}/feed
    as /api/cwebber/feed would get cwebber's profile. This
    will return a tuple (username, user_profile). If no user
    can be found then this function returns a (None, None).
    """
    username = request.matchdict["username"]
    user = User.query.filter_by(username=username).first()

    if user is None:
        return None, None

    return user, user.serialize(request)


# Endpoints
@oauth_required
def profile_endpoint(request):
    """ This is /api/user/<username>/profile - This will give profile info """
    user, user_profile = get_profile(request)

    if user is None:
        username = request.matchdict["username"]
        return json_error(
            "No such 'user' with username '{0}'".format(username),
            status=404
        )

    # user profiles are public so return information
    return json_response(user_profile)

@oauth_required
def user_endpoint(request):
    """ This is /api/user/<username> - This will get the user """
    user, user_profile = get_profile(request)

    if user is None:
        username = request.matchdict["username"]
        return json_error(
            "No such 'user' with username '{0}'".format(username),
            status=404
        )

    return json_response({
        "nickname": user.username,
        "updated": user.created.isoformat(),
        "published": user.created.isoformat(),
        "profile": user_profile,
    })

@oauth_required
@csrf_exempt
@user_has_privilege(u'uploader')
def uploads_endpoint(request):
    """ Endpoint for file uploads """
    username = request.matchdict["username"]
    requested_user = User.query.filter_by(username=username).first()

    if requested_user is None:
        return json_error("No such 'user' with id '{0}'".format(username), 404)

    if request.method == "POST":
        # Ensure that the user is only able to upload to their own
        # upload endpoint.
        if requested_user.id != request.user.id:
            return json_error(
                "Not able to post to another users feed.",
                status=403
            )

        # Wrap the data in the werkzeug file wrapper
        if "Content-Type" not in request.headers:
            return json_error(
                "Must supply 'Content-Type' header to upload media."
            )

        mimetype = request.headers["Content-Type"]
        filename = mimetypes.guess_all_extensions(mimetype)
        filename = 'unknown' + filename[0] if filename else filename
        file_data = FileStorage(
            stream=io.BytesIO(request.data),
            filename=filename,
            content_type=mimetype
        )

        # Find media manager
        entry = new_upload_entry(request.user)
        entry.media_type = IMAGE_MEDIA_TYPE
        return api_upload_request(request, file_data, entry)

    return json_error("Not yet implemented", 501)

@oauth_required
@csrf_exempt
def inbox_endpoint(request, inbox=None):
    """ This is the user's inbox

    Currently because we don't have the ability to represent the inbox in the
    database this is not a "real" inbox in the pump.io/Activity streams 1.0
    sense but instead just gives back all the data on the website

    inbox: allows you to pass a query in to limit inbox scope
    """
    username = request.matchdict["username"]
    user = User.query.filter_by(username=username).first()

    if user is None:
        return json_error("No such 'user' with id '{0}'".format(username), 404)


    # Only the user who's authorized should be able to read their inbox
    if user.id != request.user.id:
        return json_error(
            "Only '{0}' can read this inbox.".format(user.username),
            403
        )

    if inbox is None:
        inbox = Activity.query.all()

    # We want to make a query for all media on the site and then apply GET
    # limits where we can.
    inbox = inbox.order_by(Activity.published.desc())

    # Limit by the "count" (default: 20)
    inbox = inbox.limit(request.args.get("count", 20))

    # Offset (default: no offset - first <count> results)
    inbox = inbox.offset(request.args.get("offset", 0))

    # build the inbox feed
    feed = {
        "displayName": "Activities for {0}".format(user.username),
        "author": user.serialize(request),
        "objectTypes": ["activity"],
        "url": request.base_url,
        "links": {"self": {"href": request.url}},
        "items": [],
    }

    for activity in inbox:
        try:
            feed["items"].append(activity.serialize(request))
        except AttributeError:
            # As with the feed endpint this occurs because of how we our
            # hard-deletion method. Some activites might exist where the
            # Activity object and/or target no longer exist, for this case we
            # should just skip them.
            pass

    feed["totalItems"] = len(feed["items"])
    return json_response(feed)

@oauth_required
@csrf_exempt
def inbox_minor_endpoint(request):
    """ Inbox subset for less important Activities """
    inbox = Activity.query.filter(
        (Activity.verb == "update") | (Activity.verb == "delete")
    )

    return inbox_endpoint(request=request, inbox=inbox)

@oauth_required
@csrf_exempt
def inbox_major_endpoint(request):
    """ Inbox subset for most important Activities """
    inbox = Activity.query.filter_by(verb="post")
    return inbox_endpoint(request=request, inbox=inbox)

@oauth_required
@csrf_exempt
def feed_endpoint(request):
    """ Handles the user's outbox - /api/user/<username>/feed """
    username = request.matchdict["username"]
    requested_user = User.query.filter_by(username=username).first()

    # check if the user exists
    if requested_user is None:
        return json_error("No such 'user' with id '{0}'".format(username), 404)

    if request.data:
        data = json.loads(request.data.decode())
    else:
        data = {"verb": None, "object": {}}


    if request.method in ["POST", "PUT"]:
        # Validate that the activity is valid
        if "verb" not in data or "object" not in data:
            return json_error("Invalid activity provided.")

        # Check that the verb is valid
        if data["verb"] not in ["post", "update"]:
            return json_error("Verb not yet implemented", 501)

        # We need to check that the user they're posting to is
        # the person that they are.
        if requested_user.id != request.user.id:
            return json_error(
                "Not able to post to another users feed.",
                status=403
            )

        # Handle new posts
        if data["verb"] == "post":
            obj = data.get("object", None)
            if obj is None:
                return json_error("Could not find 'object' element.")

            if obj.get("objectType", None) == "comment":
                # post a comment
                if not request.user.has_privilege(u'commenter'):
                    return json_error(
                        "Privilege 'commenter' required to comment.",
                        status=403
                    )

                comment = MediaComment(author=request.user.id)
                comment.unserialize(data["object"], request)
                comment.save()

                # Create activity for comment
                generator = create_generator(request)
                activity = create_activity(
                    verb="post",
                    actor=request.user,
                    obj=comment,
                    target=comment.get_entry,
                    generator=generator
                )

                return json_response(activity.serialize(request))

            elif obj.get("objectType", None) == "image":
                # Posting an image to the feed
                media_id = int(extract_url_arguments(
                    url=data["object"]["id"],
                    urlmap=request.app.url_map
                )["id"])

                media = MediaEntry.query.filter_by(id=media_id).first()

                if media is None:
                    return json_response(
                        "No such 'image' with id '{0}'".format(media_id),
                        status=404
                    )

                if media.uploader != request.user.id:
                    return json_error(
                        "Privilege 'commenter' required to comment.",
                        status=403
                    )


                if not media.unserialize(data["object"]):
                    return json_error(
                        "Invalid 'image' with id '{0}'".format(media_id)
                    )


                # Add location if one exists
                if "location" in data:
                    Location.create(data["location"], self)

                media.save()
                activity = api_add_to_feed(request, media)

                return json_response(activity.serialize(request))

            elif obj.get("objectType", None) is None:
                # They need to tell us what type of object they're giving us.
                return json_error("No objectType specified.")
            else:
                # Oh no! We don't know about this type of object (yet)
                object_type = obj.get("objectType", None)
                return json_error(
                    "Unknown object type '{0}'.".format(object_type)
                )

        # Updating existing objects
        if data["verb"] == "update":
            # Check we've got a valid object
            obj = data.get("object", None)

            if obj is None:
                return json_error("Could not find 'object' element.")

            if "objectType" not in obj:
                return json_error("No objectType specified.")

            if "id" not in obj:
                return json_error("Object ID has not been specified.")

            obj_id = int(extract_url_arguments(
                url=obj["id"],
                urlmap=request.app.url_map
            )["id"])

            # Now try and find object
            if obj["objectType"] == "comment":
                if not request.user.has_privilege(u'commenter'):
                    return json_error(
                        "Privilege 'commenter' required to comment.",
                        status=403
                    )

                comment = MediaComment.query.filter_by(id=obj_id).first()
                if comment is None:
                    return json_error(
                        "No such 'comment' with id '{0}'.".format(obj_id)
                    )

                # Check that the person trying to update the comment is
                # the author of the comment.
                if comment.author != request.user.id:
                    return json_error(
                        "Only author of comment is able to update comment.",
                        status=403
                    )

                if not comment.unserialize(data["object"]):
                    return json_error(
                        "Invalid 'comment' with id '{0}'".format(obj_id)
                    )

                comment.save()

                # Create an update activity
                generator = create_generator(request)
                activity = create_activity(
                    verb="update",
                    actor=request.user,
                    obj=comment,
                    generator=generator
                )

                return json_response(activity.serialize(request))

            elif obj["objectType"] == "image":
                image = MediaEntry.query.filter_by(id=obj_id).first()
                if image is None:
                    return json_error(
                        "No such 'image' with the id '{0}'.".format(obj_id)
                    )

                # Check that the person trying to update the comment is
                # the author of the comment.
                if image.uploader != request.user.id:
                    return json_error(
                        "Only uploader of image is able to update image.",
                        status=403
                    )

                if not image.unserialize(obj):
                    return json_error(
                        "Invalid 'image' with id '{0}'".format(obj_id)
                    )
                image.generate_slug()
                image.save()

                # Create an update activity
                generator = create_generator(request)
                activity = create_activity(
                    verb="update",
                    actor=request.user,
                    obj=image,
                    generator=generator
                )

                return json_response(activity.serialize(request))
            elif obj["objectType"] == "person":
                # check this is the same user
                if "id" not in obj or obj["id"] != requested_user.id:
                    return json_error(
                        "Incorrect user id, unable to update"
                    )

                requested_user.unserialize(obj)
                requested_user.save()

                generator = create_generator(request)
                activity = create_activity(
                    verb="update",
                    actor=request.user,
                    obj=requested_user,
                    generator=generator
                )

                return json_response(activity.serialize(request))

    elif request.method != "GET":
        return json_error(
            "Unsupported HTTP method {0}".format(request.method),
            status=501
        )

    feed = {
        "displayName": "Activities by {user}@{host}".format(
            user=request.user.username,
            host=request.host
        ),
        "objectTypes": ["activity"],
        "url": request.base_url,
        "links": {"self": {"href": request.url}},
        "author": request.user.serialize(request),
        "items": [],
    }

    # Create outbox
    outbox = Activity.query.filter_by(actor=request.user.id)

    # We want the newest things at the top (issue: #1055)
    outbox = outbox.order_by(Activity.published.desc())

    # Limit by the "count" (default: 20)
    outbox = outbox.limit(request.args.get("count", 20))

    # Offset (default: no offset - first <count>  result)
    outbox = outbox.offset(request.args.get("offset", 0))

    # Build feed.
    for activity in outbox:
        try:
            feed["items"].append(activity.serialize(request))
        except AttributeError:
            # This occurs because of how we hard-deletion and the object
            # no longer existing anymore. We want to keep the Activity
            # in case someone wishes to look it up but we shouldn't display
            # it in the feed.
            pass
    feed["totalItems"] = len(feed["items"])

    return json_response(feed)

@oauth_required
def object_endpoint(request):
    """ Lookup for a object type """
    object_type = request.matchdict["object_type"]
    try:
        object_id = request.matchdict["id"]
    except ValueError:
        error = "Invalid object ID '{0}' for '{1}'".format(
            request.matchdict["id"],
            object_type
        )
        return json_error(error)

    if object_type not in ["image"]:
        # not sure why this is 404, maybe ask evan. Maybe 400?
        return json_error(
            "Unknown type: {0}".format(object_type),
            status=404
        )

    media = MediaEntry.query.filter_by(id=object_id).first()
    if media is None:
        return json_error(
            "Can't find '{0}' with ID '{1}'".format(object_type, object_id),
            status=404
        )

    return json_response(media.serialize(request))

@oauth_required
def object_comments(request):
    """ Looks up for the comments on a object """
    media = MediaEntry.query.filter_by(id=request.matchdict["id"]).first()
    if media is None:
        return json_error("Can't find '{0}' with ID '{1}'".format(
            request.matchdict["object_type"],
            request.matchdict["id"]
        ), 404)

    comments = media.serialize(request)
    comments = comments.get("replies", {
        "totalItems": 0,
        "items": [],
        "url": request.urlgen(
            "mediagoblin.federation.object.comments",
            object_type=media.object_type,
            id=media.id,
            qualified=True
        )
    })

    comments["displayName"] = "Replies to {0}".format(comments["url"])
    comments["links"] = {
        "first": comments["url"],
        "self": comments["url"],
    }
    return json_response(comments)

##
# RFC6415 - Web Host Metadata
##
def host_meta(request):
    """
    This provides the host-meta URL information that is outlined
    in RFC6415. By default this should provide XRD+XML however
    if the client accepts JSON we will provide that over XRD+XML.
    The 'Accept' header is used to decude this.

    A client should use this endpoint to determine what URLs to
    use for OAuth endpoints.
    """

    links = [
        {
            "rel": "lrdd",
            "type": "application/json",
            "href": request.urlgen(
                "mediagoblin.webfinger.well-known.webfinger",
                qualified=True
            )
        },
        {
            "rel": "registration_endpoint",
            "href": request.urlgen(
                "mediagoblin.oauth.client_register",
                qualified=True
            ),
        },
        {
            "rel": "http://apinamespace.org/oauth/request_token",
            "href": request.urlgen(
                "mediagoblin.oauth.request_token",
                qualified=True
            ),
        },
        {
            "rel": "http://apinamespace.org/oauth/authorize",
            "href": request.urlgen(
                "mediagoblin.oauth.authorize",
                qualified=True
            ),
        },
        {
            "rel": "http://apinamespace.org/oauth/access_token",
            "href": request.urlgen(
                "mediagoblin.oauth.access_token",
                qualified=True
            ),
        },
        {
            "rel": "http://apinamespace.org/activitypub/whoami",
            "href": request.urlgen(
                "mediagoblin.webfinger.whoami",
                qualified=True
            ),
        },
    ]

    if "application/json" in request.accept_mimetypes:
        return json_response({"links": links})

    # provide XML+XRD
    return render_to_response(
        request,
        "mediagoblin/federation/host-meta.xml",
        {"links": links},
        mimetype="application/xrd+xml"
    )

def lrdd_lookup(request):
    """
    This is the lrdd endpoint which can lookup a user (or
    other things such as activities). This is as specified by
    RFC6415.

    The cleint must provide a 'resource' as a GET parameter which
    should be the query to be looked up.
    """

    if "resource" not in request.args:
        return json_error("No resource parameter", status=400)

    resource = request.args["resource"]

    if "@" in resource:
        # Lets pull out the username
        resource = resource[5:] if resource.startswith("acct:") else resource
        username, host = resource.split("@", 1)

        # Now lookup the user
        user = User.query.filter_by(username=username).first()

        if user is None:
            return json_error(
                "Can't find 'user' with username '{0}'".format(username))

        return json_response([
            {
                "rel": "http://webfinger.net/rel/profile-page",
                "href": user.url_for_self(request.urlgen),
                "type": "text/html"
            },
            {
                "rel": "self",
                "href": request.urlgen(
                    "mediagoblin.federation.user",
                    username=user.username,
                    qualified=True
                )
            },
            {
                "rel": "activity-outbox",
                "href": request.urlgen(
                    "mediagoblin.federation.feed",
                    username=user.username,
                    qualified=True
                )
            }
        ])
    else:
        return json_error("Unrecognized resource parameter", status=404)


def whoami(request):
    """ /api/whoami - HTTP redirect to API profile """
    if request.user is None:
        return json_error("Not logged in.", status=401)

    profile = request.urlgen(
        "mediagoblin.federation.user.profile",
        username=request.user.username,
        qualified=True
    )

    return redirect(request, location=profile)

@require_active_login
def activity_view(request):
    """ /<username>/activity/<id> - Display activity

    This should display a HTML presentation of the activity
    this is NOT an API endpoint.
    """
    # Get the user object.
    username = request.matchdict["username"]
    user = User.query.filter_by(username=username).first()

    activity_id = request.matchdict["id"]

    if request.user is None:
        return render_404(request)

    activity = Activity.query.filter_by(
        id=activity_id,
        author=user.id
    ).first()
    if activity is None:
        return render_404(request)

    return render_to_response(
        request,
        "mediagoblin/federation/activity.html",
        {"activity": activity}
    )


