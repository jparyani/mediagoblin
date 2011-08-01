# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 Free Software Foundation, Inc
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

from mediagoblin.db.util import DESCENDING

from mediagoblin.util import Pagination, render_to_response
from mediagoblin.decorators import uses_pagination


@uses_pagination
def tag_listing(request, page):
    """'Gallery'/listing for this tag slug"""
    tag_slug = request.matchdict[u'tag']

    cursor = request.db.MediaEntry.find(
        {u'state': u'processed',
         u'tags.slug': tag_slug})
    cursor = cursor.sort('created', DESCENDING)
         
    pagination = Pagination(page, cursor)
    media_entries = pagination()

    # Take the tag "name" from the first MediaEntry's non-normalized
    # tag naming.
    # ... this is slightly hacky looking :\
    tag_name = tag_slug
    if media_entries.count():
        for tag in media_entries[0]['tags']:
            if tag['slug'] == tag_slug:
                tag_name == tag['name']
                break
    else:
        tag_name = tag_slug

    return render_to_response(
        request,
        'mediagoblin/listings/tag.html',
        {'tag_name': tag_name,
         'media_entries': media_entries,
         'pagination': pagination})
