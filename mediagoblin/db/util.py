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

try:
    from mediagoblin.db.sql_switch import use_sql
except ImportError:
    use_sql = False

if use_sql:
    from mediagoblin.db.sql.fake import ObjectId, InvalidId, DESCENDING
    from mediagoblin.db.sql.util import atomic_update, check_media_slug_used, \
        media_entries_for_tag_slug, check_collection_slug_used
else:
    from mediagoblin.db.mongo.util import \
        ObjectId, InvalidId, DESCENDING, atomic_update, \
        check_media_slug_used, media_entries_for_tag_slug
