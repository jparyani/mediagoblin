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

import logging
import datetime

from mediagoblin import messages, mg_globals
from mediagoblin.db.models import (MediaEntry, MediaTag, Collection,
                                   CollectionItem, User)
from mediagoblin.tools.response import render_to_response, render_404, \
    redirect, redirect_obj
from mediagoblin.tools.translate import pass_to_ugettext as _
from mediagoblin.tools.pagination import Pagination
from mediagoblin.user_pages import forms as user_forms
from mediagoblin.user_pages.lib import add_media_to_collection
from mediagoblin.notifications import trigger_notification, \
    add_comment_subscription, mark_comment_notification_seen

from mediagoblin.decorators import (uses_pagination, get_user_media_entry,
    get_media_entry_by_id,
    require_active_login, user_may_delete_media, user_may_alter_collection,
    get_user_collection, get_user_collection_item, active_user_from_url)

from werkzeug.contrib.atom import AtomFeed
from werkzeug.exceptions import MethodNotAllowed


_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)


@uses_pagination
def user_home(request, page):
    """'Homepage' of a User()"""
    # TODO: decide if we only want homepages for active users, we can
    # then use the @get_active_user decorator and also simplify the
    # template html.
    user = User.query.filter_by(username=request.matchdict['user']).first()
    if not user:
        return render_404(request)
    elif user.status != u'active':
        return render_to_response(
            request,
            'mediagoblin/user_pages/user.html',
            {'user': user})

    cursor = MediaEntry.query.\
        filter_by(uploader = user.id,
                  state = u'processed').order_by(MediaEntry.created.desc())

    pagination = Pagination(page, cursor)
    media_entries = pagination()

    #if no data is available, return NotFound
    if media_entries == None:
        return render_404(request)

    user_gallery_url = request.urlgen(
        'mediagoblin.user_pages.user_gallery',
        user=user.username)

    return render_to_response(
        request,
        'mediagoblin/user_pages/user.html',
        {'user': user,
         'user_gallery_url': user_gallery_url,
         'media_entries': media_entries,
         'pagination': pagination})


@active_user_from_url
@uses_pagination
def user_gallery(request, page, url_user=None):
    """'Gallery' of a User()"""
    tag = request.matchdict.get('tag', None)
    cursor = MediaEntry.query.filter_by(
        uploader=url_user.id,
        state=u'processed').order_by(MediaEntry.created.desc())

    # Filter potentially by tag too:
    if tag:
        cursor = cursor.filter(
            MediaEntry.tags_helper.any(
                MediaTag.slug == request.matchdict['tag']))

    # Paginate gallery
    pagination = Pagination(page, cursor)
    media_entries = pagination()

    #if no data is available, return NotFound
    # TODO: Should we really also return 404 for empty galleries?
    if media_entries == None:
        return render_404(request)

    return render_to_response(
        request,
        'mediagoblin/user_pages/gallery.html',
        {'user': url_user, 'tag': tag,
         'media_entries': media_entries,
         'pagination': pagination})


MEDIA_COMMENTS_PER_PAGE = 50


@get_user_media_entry
@uses_pagination
def media_home(request, media, page, **kwargs):
    """
    'Homepage' of a MediaEntry()
    """
    comment_id = request.matchdict.get('comment', None)
    if comment_id:
        if request.user:
            mark_comment_notification_seen(comment_id, request.user)

        pagination = Pagination(
            page, media.get_comments(
                mg_globals.app_config['comments_ascending']),
            MEDIA_COMMENTS_PER_PAGE,
            comment_id)
    else:
        pagination = Pagination(
            page, media.get_comments(
                mg_globals.app_config['comments_ascending']),
            MEDIA_COMMENTS_PER_PAGE)

    comments = pagination()

    comment_form = user_forms.MediaCommentForm(request.form)

    media_template_name = media.media_manager.display_template

    return render_to_response(
        request,
        media_template_name,
        {'media': media,
         'comments': comments,
         'pagination': pagination,
         'comment_form': comment_form,
         'app_config': mg_globals.app_config})


@get_media_entry_by_id
@require_active_login
def media_post_comment(request, media):
    """
    recieves POST from a MediaEntry() comment form, saves the comment.
    """
    if not request.method == 'POST':
        raise MethodNotAllowed()

    comment = request.db.MediaComment()
    comment.media_entry = media.id
    comment.author = request.user.id
    comment.content = unicode(request.form['comment_content'])

    # Show error message if commenting is disabled.
    if not mg_globals.app_config['allow_comments']:
        messages.add_message(
            request,
            messages.ERROR,
            _("Sorry, comments are disabled."))
    elif not comment.content.strip():
        messages.add_message(
            request,
            messages.ERROR,
            _("Oops, your comment was empty."))
    else:
        comment.save()

        messages.add_message(
            request, messages.SUCCESS,
            _('Your comment has been posted!'))

        trigger_notification(comment, media, request)

        add_comment_subscription(request.user, media)

    return redirect_obj(request, media)


@get_media_entry_by_id
@require_active_login
def media_collect(request, media):
    """Add media to collection submission"""

    form = user_forms.MediaCollectForm(request.form)
    # A user's own collections:
    form.collection.query = Collection.query.filter_by(
        creator = request.user.id).order_by(Collection.title)

    if request.method != 'POST' or not form.validate():
        # No POST submission, or invalid form
        if not form.validate():
            messages.add_message(request, messages.ERROR,
                _('Please check your entries and try again.'))

        return render_to_response(
            request,
            'mediagoblin/user_pages/media_collect.html',
            {'media': media,
             'form': form})

    # If we are here, method=POST and the form is valid, submit things.
    # If the user is adding a new collection, use that:
    if form.collection_title.data:
        # Make sure this user isn't duplicating an existing collection
        existing_collection = Collection.query.filter_by(
                                creator=request.user.id,
                                title=form.collection_title.data).first()
        if existing_collection:
            messages.add_message(request, messages.ERROR,
                _('You already have a collection called "%s"!')
                % existing_collection.title)
            return redirect(request, "mediagoblin.user_pages.media_home",
                            user=media.get_uploader.username,
                            media=media.slug_or_id)

        collection = Collection()
        collection.title = form.collection_title.data
        collection.description = form.collection_description.data
        collection.creator = request.user.id
        collection.generate_slug()
        collection.save()

    # Otherwise, use the collection selected from the drop-down
    else:
        collection = form.collection.data
        if collection and collection.creator != request.user.id:
            collection = None

    # Make sure the user actually selected a collection
    if not collection:
        messages.add_message(
            request, messages.ERROR,
            _('You have to select or add a collection'))
        return redirect(request, "mediagoblin.user_pages.media_collect",
                    user=media.get_uploader.username,
                    media_id=media.id)


    # Check whether media already exists in collection
    elif CollectionItem.query.filter_by(
        media_entry=media.id,
        collection=collection.id).first():
        messages.add_message(request, messages.ERROR,
                             _('"%s" already in collection "%s"')
                             % (media.title, collection.title))
    else: # Add item to collection
        add_media_to_collection(collection, media, form.note.data)

        messages.add_message(request, messages.SUCCESS,
                             _('"%s" added to collection "%s"')
                             % (media.title, collection.title))

    return redirect_obj(request, media)


#TODO: Why does @user_may_delete_media not implicate @require_active_login?
@get_media_entry_by_id
@require_active_login
@user_may_delete_media
def media_confirm_delete(request, media):

    form = user_forms.ConfirmDeleteForm(request.form)

    if request.method == 'POST' and form.validate():
        if form.confirm.data is True:
            username = media.get_uploader.username
            # Delete MediaEntry and all related files, comments etc.
            media.delete()
            messages.add_message(
                request, messages.SUCCESS, _('You deleted the media.'))

            return redirect(request, "mediagoblin.user_pages.user_home",
                user=username)
        else:
            messages.add_message(
                request, messages.ERROR,
                _("The media was not deleted because you didn't check that you were sure."))
            return redirect_obj(request, media)

    if ((request.user.is_admin and
         request.user.id != media.uploader)):
        messages.add_message(
            request, messages.WARNING,
            _("You are about to delete another user's media. "
              "Proceed with caution."))

    return render_to_response(
        request,
        'mediagoblin/user_pages/media_confirm_delete.html',
        {'media': media,
         'form': form})


@active_user_from_url
@uses_pagination
def user_collection(request, page, url_user=None):
    """A User-defined Collection"""
    collection = Collection.query.filter_by(
        get_creator=url_user,
        slug=request.matchdict['collection']).first()

    if not collection:
        return render_404(request)

    cursor = collection.get_collection_items()

    pagination = Pagination(page, cursor)
    collection_items = pagination()

    # if no data is available, return NotFound
    # TODO: Should an empty collection really also return 404?
    if collection_items == None:
        return render_404(request)

    return render_to_response(
        request,
        'mediagoblin/user_pages/collection.html',
        {'user': url_user,
         'collection': collection,
         'collection_items': collection_items,
         'pagination': pagination})


@active_user_from_url
def collection_list(request, url_user=None):
    """A User-defined Collection"""
    collections = Collection.query.filter_by(
        get_creator=url_user)

    return render_to_response(
        request,
        'mediagoblin/user_pages/collection_list.html',
        {'user': url_user,
         'collections': collections})


@get_user_collection_item
@require_active_login
@user_may_alter_collection
def collection_item_confirm_remove(request, collection_item):

    form = user_forms.ConfirmCollectionItemRemoveForm(request.form)

    if request.method == 'POST' and form.validate():
        username = collection_item.in_collection.get_creator.username
        collection = collection_item.in_collection

        if form.confirm.data is True:
            entry = collection_item.get_media_entry
            entry.collected = entry.collected - 1
            entry.save()

            collection_item.delete()
            collection.items = collection.items - 1
            collection.save()

            messages.add_message(
                request, messages.SUCCESS, _('You deleted the item from the collection.'))
        else:
            messages.add_message(
                request, messages.ERROR,
                _("The item was not removed because you didn't check that you were sure."))

        return redirect_obj(request, collection)

    if ((request.user.is_admin and
         request.user.id != collection_item.in_collection.creator)):
        messages.add_message(
            request, messages.WARNING,
            _("You are about to delete an item from another user's collection. "
              "Proceed with caution."))

    return render_to_response(
        request,
        'mediagoblin/user_pages/collection_item_confirm_remove.html',
        {'collection_item': collection_item,
         'form': form})


@get_user_collection
@require_active_login
@user_may_alter_collection
def collection_confirm_delete(request, collection):

    form = user_forms.ConfirmDeleteForm(request.form)

    if request.method == 'POST' and form.validate():

        username = collection.get_creator.username

        if form.confirm.data is True:
            collection_title = collection.title

            # Delete all the associated collection items
            for item in collection.get_collection_items():
                entry = item.get_media_entry
                entry.collected = entry.collected - 1
                entry.save()
                item.delete()

            collection.delete()
            messages.add_message(request, messages.SUCCESS,
                _('You deleted the collection "%s"') % collection_title)

            return redirect(request, "mediagoblin.user_pages.user_home",
                user=username)
        else:
            messages.add_message(
                request, messages.ERROR,
                _("The collection was not deleted because you didn't check that you were sure."))

            return redirect_obj(request, collection)

    if ((request.user.is_admin and
         request.user.id != collection.creator)):
        messages.add_message(
            request, messages.WARNING,
            _("You are about to delete another user's collection. "
              "Proceed with caution."))

    return render_to_response(
        request,
        'mediagoblin/user_pages/collection_confirm_delete.html',
        {'collection': collection,
         'form': form})


ATOM_DEFAULT_NR_OF_UPDATED_ITEMS = 15


def atom_feed(request):
    """
    generates the atom feed with the newest images
    """
    user = User.query.filter_by(
        username = request.matchdict['user'],
        status = u'active').first()
    if not user:
        return render_404(request)

    cursor = MediaEntry.query.filter_by(
        uploader = user.id,
        state = u'processed').\
        order_by(MediaEntry.created.desc()).\
        limit(ATOM_DEFAULT_NR_OF_UPDATED_ITEMS)

    """
    ATOM feed id is a tag URI (see http://en.wikipedia.org/wiki/Tag_URI)
    """
    atomlinks = [{
           'href': request.urlgen(
               'mediagoblin.user_pages.user_home',
               qualified=True, user=request.matchdict['user']),
           'rel': 'alternate',
           'type': 'text/html'
           }]

    if mg_globals.app_config["push_urls"]:
        for push_url in mg_globals.app_config["push_urls"]:
            atomlinks.append({
                'rel': 'hub',
                'href': push_url})

    feed = AtomFeed(
               "MediaGoblin: Feed for user '%s'" % request.matchdict['user'],
               feed_url=request.url,
               id='tag:{host},{year}:gallery.user-{user}'.format(
                   host=request.host,
                   year=datetime.datetime.today().strftime('%Y'),
                   user=request.matchdict['user']),
               links=atomlinks)

    for entry in cursor:
        feed.add(entry.get('title'),
            entry.description_html,
            id=entry.url_for_self(request.urlgen, qualified=True),
            content_type='html',
            author={
                'name': entry.get_uploader.username,
                'uri': request.urlgen(
                    'mediagoblin.user_pages.user_home',
                    qualified=True, user=entry.get_uploader.username)},
            updated=entry.get('created'),
            links=[{
                'href': entry.url_for_self(
                    request.urlgen,
                    qualified=True),
                'rel': 'alternate',
                'type': 'text/html'}])

    return feed.get_response()


def collection_atom_feed(request):
    """
    generates the atom feed with the newest images from a collection
    """
    user = User.query.filter_by(
        username = request.matchdict['user'],
        status = u'active').first()
    if not user:
        return render_404(request)

    collection = Collection.query.filter_by(
               creator=user.id,
               slug=request.matchdict['collection']).first()
    if not collection:
        return render_404(request)

    cursor = CollectionItem.query.filter_by(
                 collection=collection.id) \
                 .order_by(CollectionItem.added.desc()) \
                 .limit(ATOM_DEFAULT_NR_OF_UPDATED_ITEMS)

    """
    ATOM feed id is a tag URI (see http://en.wikipedia.org/wiki/Tag_URI)
    """
    atomlinks = [{
           'href': collection.url_for_self(request.urlgen, qualified=True),
           'rel': 'alternate',
           'type': 'text/html'
           }]

    if mg_globals.app_config["push_urls"]:
        for push_url in mg_globals.app_config["push_urls"]:
            atomlinks.append({
                'rel': 'hub',
                'href': push_url})

    feed = AtomFeed(
                "MediaGoblin: Feed for %s's collection %s" %
                (request.matchdict['user'], collection.title),
                feed_url=request.url,
                id=u'tag:{host},{year}:gnu-mediagoblin.{user}.collection.{slug}'\
                    .format(
                    host=request.host,
                    year=collection.created.strftime('%Y'),
                    user=request.matchdict['user'],
                    slug=collection.slug),
                links=atomlinks)

    for item in cursor:
        entry = item.get_media_entry
        feed.add(entry.get('title'),
            item.note_html,
            id=entry.url_for_self(request.urlgen, qualified=True),
            content_type='html',
            author={
                'name': entry.get_uploader.username,
                'uri': request.urlgen(
                    'mediagoblin.user_pages.user_home',
                    qualified=True, user=entry.get_uploader.username)},
            updated=item.get('added'),
            links=[{
                'href': entry.url_for_self(
                    request.urlgen,
                    qualified=True),
                'rel': 'alternate',
                'type': 'text/html'}])

    return feed.get_response()


@require_active_login
def processing_panel(request):
    """
    Show to the user what media is still in conversion/processing...
    and what failed, and why!
    """
    user = User.query.filter_by(username=request.matchdict['user']).first()
    # TODO: XXX: Should this be a decorator?
    #
    # Make sure we have permission to access this user's panel.  Only
    # admins and this user herself should be able to do so.
    if not (user.id == request.user.id or request.user.is_admin):
        # No?  Simply redirect to this user's homepage.
        return redirect(
            request, 'mediagoblin.user_pages.user_home',
            user=user.username)

    # Get media entries which are in-processing
    processing_entries = MediaEntry.query.\
        filter_by(uploader = user.id,
                  state = u'processing').\
        order_by(MediaEntry.created.desc())

    # Get media entries which have failed to process
    failed_entries = MediaEntry.query.\
        filter_by(uploader = user.id,
                  state = u'failed').\
        order_by(MediaEntry.created.desc())

    processed_entries = MediaEntry.query.\
        filter_by(uploader = user.id,
                  state = u'processed').\
        order_by(MediaEntry.created.desc()).\
        limit(10)

    # Render to response
    return render_to_response(
        request,
        'mediagoblin/user_pages/processing_panel.html',
        {'user': user,
         'processing_entries': processing_entries,
         'failed_entries': failed_entries,
         'processed_entries': processed_entries})
