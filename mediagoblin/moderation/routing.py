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

moderation_routes = [
    ('mediagoblin.moderation.media_panel',
        '/media/',
        'mediagoblin.moderation.views:moderation_media_processing_panel'),
    ('mediagoblin.moderation.users',
        '/users/',
        'mediagoblin.moderation.views:moderation_users_panel'),
    ('mediagoblin.moderation.reports',
        '/reports/',
        'mediagoblin.moderation.views:moderation_reports_panel'),
    ('mediagoblin.moderation.users_detail',
        '/users/<string:user>/',
        'mediagoblin.moderation.views:moderation_users_detail'),
    ('mediagoblin.moderation.give_or_take_away_privilege',
        '/users/<string:user>/privilege/',
        'mediagoblin.moderation.views:give_or_take_away_privilege'),
    ('mediagoblin.moderation.ban_or_unban',
        '/users/<string:user>/ban/',
        'mediagoblin.moderation.views:ban_or_unban'),
    ('mediagoblin.moderation.reports_detail',
        '/reports/<int:report_id>/',
        'mediagoblin.moderation.views:moderation_reports_detail')]
