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

from webob import Response, exc
from mediagoblin.db.util import DESCENDING
from mediagoblin.util import Pagination

from mediagoblin.decorators import uses_pagination, get_user_media_entry

from werkzeug.contrib.atom import AtomFeed

@uses_pagination
def user_home(request, page):
    """'Homepage' of a User()"""
    user = request.db.User.find_one({
            'username': request.matchdict['user'],
            'status': 'active'})
    if not user:
        return exc.HTTPNotFound()

    cursor = request.db.MediaEntry.find(
        {'uploader': user['_id'],
         'state': 'processed'}).sort('created', DESCENDING)

    pagination = Pagination(page, cursor)
    media_entries = pagination()

    #if no data is available, return NotFound
    if media_entries == None:
        return exc.HTTPNotFound()
    
    template = request.template_env.get_template(
        'mediagoblin/user_pages/user.html')

    return Response(
        template.render(
            {'request': request,
             'user': user,
             'media_entries': media_entries,
             'pagination': pagination}))


@get_user_media_entry
def media_home(request, media):
    """'Homepage' of a MediaEntry()"""
    template = request.template_env.get_template(
        'mediagoblin/user_pages/media.html')
    return Response(
        template.render(
            {'request': request,
             'media': media}))

ATOM_DEFAULT_NR_OF_UPDATED_ITEMS = 5

def atom_feed(request):
    """
    generates the atom feed with the newest images
    """

    user = request.db.User.find_one({
               'username': request.matchdict['user'],
               'status': 'active'})
    if not user:
	return exc.HTTPNotFound()

    cursor = request.db.MediaEntry.find({
                 'uploader': user['_id'],
                 'state': 'processed'}) \
                 .sort('created', DESCENDING) \
                 .limit(ATOM_DEFAULT_NR_OF_UPDATED_ITEMS)

    feed = AtomFeed(request.matchdict['user'],
               feed_url=request.url,
               url=request.host_url)
            
    for entry in cursor:
        feed.add(entry.get('title'),
            entry.get('description'),
            content_type='html',
            author=request.matchdict['user'],
            updated=entry.get('created'),
            url=entry.url_for_self(request.urlgen))

    return feed.get_response() 
