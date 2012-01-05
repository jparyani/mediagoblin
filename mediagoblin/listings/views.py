# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 MediaGoblin contributors.  See AUTHORS.
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

from mediagoblin.tools.pagination import Pagination
from mediagoblin.tools.response import render_to_response
from mediagoblin.decorators import uses_pagination

from werkzeug.contrib.atom import AtomFeed


def _get_tag_name_from_entries(media_entries, tag_slug):
    """
    Get a tag name from the first entry by looking it up via its slug.
    """
    # ... this is slightly hacky looking :\
    tag_name = tag_slug
    if media_entries.count():
        for tag in media_entries[0]['tags']:
            if tag['slug'] == tag_slug:
                tag_name == tag['name']
                break

    return tag_name


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

    tag_name = _get_tag_name_from_entries(media_entries, tag_slug)

    return render_to_response(
        request,
        'mediagoblin/listings/tag.html',
        {'tag_slug': tag_slug,
         'tag_name': tag_name,
         'media_entries': media_entries,
         'pagination': pagination})


ATOM_DEFAULT_NR_OF_UPDATED_ITEMS = 15


def tag_atom_feed(request):
    """
    generates the atom feed with the tag images
    """
    tag_slug = request.matchdict[u'tag']

    cursor = request.db.MediaEntry.find(
        {u'state': u'processed',
         u'tags.slug': tag_slug})
    cursor = cursor.sort('created', DESCENDING)
    cursor = cursor.limit(ATOM_DEFAULT_NR_OF_UPDATED_ITEMS)

    """
    ATOM feed id is a tag URI (see http://en.wikipedia.org/wiki/Tag_URI)
    """
    feed = AtomFeed(
        "MediaGoblin: Feed for tag '%s'" % tag_slug,
        feed_url=request.url,
        id='tag:'+request.host+',2011:gallery.tag-%s' % tag_slug,
        links=[{'href': request.urlgen(
                 'mediagoblin.listings.tags_listing',
                 qualified=True, tag=tag_slug ),
            'rel': 'alternate',
            'type': 'text/html'}])
    for entry in cursor:
        feed.add(entry.get('title'),
            entry.get('description_html'),
            id=entry.url_for_self(request.urlgen,qualified=True),
            content_type='html',
            author={'name': entry.get_uploader.username,
                'uri': request.urlgen(
                    'mediagoblin.user_pages.user_home',
                    qualified=True, user=entry.get_uploader.username)},
            updated=entry.get('created'),
            links=[{
                'href':entry.url_for_self(
                   request.urlgen,
                   qualified=True),
                'rel': 'alternate',
                'type': 'text/html'}])

    return feed.get_response()
