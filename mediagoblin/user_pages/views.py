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

from webob import exc

from mediagoblin import messages
from mediagoblin.db.util import DESCENDING, ObjectId
from mediagoblin.util import (
    Pagination, render_to_response, redirect, cleaned_markdown_conversion)
from mediagoblin.user_pages import forms as user_forms

from mediagoblin.decorators import (uses_pagination, get_user_media_entry,
    require_active_login)

from werkzeug.contrib.atom import AtomFeed


@uses_pagination
def user_home(request, page):
    """'Homepage' of a User()"""
    user = request.db.User.find_one({
            'username': request.matchdict['user']})
    if not user:
        return exc.HTTPNotFound()
    elif user['status'] != u'active':
        return render_to_response(
            request,
            'mediagoblin/user_pages/user.html',
            {'user': user})

    cursor = request.db.MediaEntry.find(
        {'uploader': user['_id'],
         'state': 'processed'}).sort('created', DESCENDING)

    pagination = Pagination(page, cursor)
    media_entries = pagination()

    #if no data is available, return NotFound
    if media_entries == None:
        return exc.HTTPNotFound()
    
    user_gallery_url = request.urlgen(
        'mediagoblin.user_pages.user_gallery',
        user=user['username'])

    return render_to_response(
        request,
        'mediagoblin/user_pages/user.html',
        {'user': user,
         'user_gallery_url': user_gallery_url,
         'media_entries': media_entries,
         'pagination': pagination})

@uses_pagination
def user_gallery(request, page):
    """'Gallery' of a User()"""
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
    
    return render_to_response(
        request,
        'mediagoblin/user_pages/gallery.html',
        {'user': user,
         'media_entries': media_entries,
         'pagination': pagination})

MEDIA_COMMENTS_PER_PAGE = 50

@get_user_media_entry
@uses_pagination
def media_home(request, media, page, **kwargs):
    """
    'Homepage' of a MediaEntry()
    """
    if ObjectId(request.matchdict.get('comment')):
        pagination = Pagination(
            page, media.get_comments(), MEDIA_COMMENTS_PER_PAGE,
            ObjectId(request.matchdict.get('comment')))
    else:
        pagination = Pagination(
            page, media.get_comments(), MEDIA_COMMENTS_PER_PAGE)

    comments = pagination()

    comment_form = user_forms.MediaCommentForm(request.POST)

    return render_to_response(
        request,
        'mediagoblin/user_pages/media.html',
        {'media': media,
         'comments': comments,
         'pagination': pagination,
         'comment_form': comment_form})


@require_active_login
def media_post_comment(request):
    """
    recieves POST from a MediaEntry() comment form, saves the comment.
    """
    comment = request.db.MediaComment()
    comment['media_entry'] = ObjectId(request.matchdict['media'])
    comment['author'] = request.user['_id']
    comment['content'] = request.POST['comment_content']

    comment['content_html'] = cleaned_markdown_conversion(comment['content'])

    comment.save()

    messages.add_message(
        request, messages.SUCCESS,
        'Comment posted!')

    return redirect(request, 'mediagoblin.user_pages.media_home',
        media = request.matchdict['media'],
        user = request.matchdict['user'])


ATOM_DEFAULT_NR_OF_UPDATED_ITEMS = 15

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
            entry.get('description_html'),
            content_type='html',
            author=request.matchdict['user'],
            updated=entry.get('created'),
            url=entry.url_for_self(request.urlgen))

    return feed.get_response()
