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

from mediagoblin.tools.routing import add_route

# Add user profile
add_route(
    "mediagoblin.federation.user",
    "/api/user/<string:username>/",
    "mediagoblin.federation.views:user_endpoint",
    match_slash=False
)

add_route(
    "mediagoblin.federation.user.profile",
    "/api/user/<string:username>/profile/",
    "mediagoblin.federation.views:profile_endpoint",
    match_slash=False
)

# Inbox and Outbox (feed)
add_route(
    "mediagoblin.federation.feed",
    "/api/user/<string:username>/feed/",
    "mediagoblin.federation.views:feed_endpoint",
    match_slash=False
)

add_route(
    "mediagoblin.federation.feed_major",
    "/api/user/<string:username>/feed/major/",
    "mediagoblin.federation.views:feed_major_endpoint",
    match_slash=False
)

add_route(
    "mediagoblin.federation.feed_minor",
    "/api/user/<string:username>/feed/minor/",
    "mediagoblin.federation.views:feed_minor_endpoint",
    match_slash=False
)

add_route(
    "mediagoblin.federation.user.uploads",
    "/api/user/<string:username>/uploads/",
    "mediagoblin.federation.views:uploads_endpoint",
    match_slash=False
)

add_route(
    "mediagoblin.federation.inbox",
    "/api/user/<string:username>/inbox/",
    "mediagoblin.federation.views:inbox_endpoint",
    match_slash=False
)

add_route(
    "mediagoblin.federation.inbox_minor",
    "/api/user/<string:username>/inbox/minor/",
    "mediagoblin.federation.views:inbox_minor_endpoint",
    match_slash=False
)

add_route(
    "mediagoblin.federation.inbox_major",
    "/api/user/<string:username>/inbox/major/",
    "mediagoblin.federation.views:inbox_major_endpoint",
    match_slash=False
)

add_route(
    "mediagoblin.federation.inbox_direct",
    "/api/user/<string:username>/inbox/direct/",
    "mediagoblin.federation.views:inbox_endpoint",
    match_slash=False
)

add_route(
    "mediagoblin.federation.inbox_direct_minor",
    "/api/user/<string:username>/inbox/direct/minor/",
    "mediagoblin.federation.views:inbox_minor_endpoint",
    match_slash=False
)

add_route(
    "mediagoblin.federation.inbox_direct_major",
    "/api/user/<string:username>/inbox/direct/major/",
    "mediagoblin.federation.views:inbox_major_endpoint",
    match_slash=False
)

# object endpoints
add_route(
    "mediagoblin.federation.object",
    "/api/<string:object_type>/<string:id>/",
    "mediagoblin.federation.views:object_endpoint",
    match_slash=False
)

add_route(
    "mediagoblin.federation.object.comments",
    "/api/<string:object_type>/<string:id>/comments/",
    "mediagoblin.federation.views:object_comments",
    match_slash=False
)

add_route(
    "mediagoblin.webfinger.well-known.host-meta",
    "/.well-known/host-meta",
    "mediagoblin.federation.views:host_meta"
)

add_route(
    "mediagoblin.webfinger.well-known.host-meta.json",
    "/.well-known/host-meta.json",
    "mediagoblin.federation.views:host_meta"
)

add_route(
    "mediagoblin.webfinger.well-known.webfinger",
    "/.well-known/webfinger/",
    "mediagoblin.federation.views:lrdd_lookup",
    match_slash=False
)

add_route(
    "mediagoblin.webfinger.whoami",
    "/api/whoami/",
    "mediagoblin.federation.views:whoami",
    match_slash=False
)

add_route(
    "mediagoblin.federation.activity_view",
    "/<string:username>/activity/<string:id>/",
    "mediagoblin.federation.views:activity_view",
    match_slash=False
)
