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

import uuid

from webob import exc
from string import split
from cgi import FieldStorage
from datetime import datetime

from werkzeug.utils import secure_filename

from mediagoblin import messages
from mediagoblin import mg_globals
from mediagoblin.util import (
    render_to_response, redirect, clean_html, convert_to_tag_list_of_dicts,
    media_tags_as_string, cleaned_markdown_conversion)
from mediagoblin.util import pass_to_ugettext as _
from mediagoblin.edit import forms
from mediagoblin.edit.lib import may_edit_media
from mediagoblin.decorators import require_active_login, get_user_media_entry


@get_user_media_entry
@require_active_login
def edit_media(request, media):
    if not may_edit_media(request, media):
        return exc.HTTPForbidden()

    defaults = dict(
        title=media['title'],
        slug=media['slug'],
        description=media['description'],
        tags=media_tags_as_string(media['tags']))

    if len(media['attachment_files']):
        defaults['attachment_name'] = media['attachment_files'][0]['name']

    form = forms.EditForm(
        request.POST,
        **defaults)

    if request.method == 'POST' and form.validate():
        # Make sure there isn't already a MediaEntry with such a slug
        # and userid.
        existing_user_slug_entries = request.db.MediaEntry.find(
            {'slug': request.POST['slug'],
             'uploader': media['uploader'],
             '_id': {'$ne': media['_id']}}).count()

        if existing_user_slug_entries:
            form.slug.errors.append(
                _(u'An entry with that slug already exists for this user.'))
        else:
            media['title'] = unicode(request.POST['title'])
            media['description'] = unicode(request.POST.get('description'))
            media['tags'] = convert_to_tag_list_of_dicts(
                                   request.POST.get('tags'))

            media['description_html'] = cleaned_markdown_conversion(
                media['description'])

            if 'attachment_name' in request.POST:
                media['attachment_files'][0]['name'] = \
                    request.POST['attachment_name']

            if 'attachment_delete' in request.POST \
                    and 'y' == request.POST['attachment_delete']:
                del media['attachment_files'][0]

            media['slug'] = unicode(request.POST['slug'])
            media.save()

            return redirect(request, "mediagoblin.user_pages.media_home",
                user=media.uploader()['username'], media=media['slug'])

    if request.user['is_admin'] \
            and media['uploader'] != request.user['_id'] \
            and request.method != 'POST':
        messages.add_message(
            request, messages.WARNING,
            _("You are editing another user's media. Proceed with caution."))

    return render_to_response(
        request,
        'mediagoblin/edit/edit.html',
        {'media': media,
         'form': form})


@get_user_media_entry
@require_active_login
def edit_attachments(request, media):
    if mg_globals.app_config['allow_attachments']:
        form = forms.EditAttachmentsForm()

        # Add any attachements
        if ('attachment_file' in request.POST
            and isinstance(request.POST['attachment_file'], FieldStorage)
            and request.POST['attachment_file'].file):

            attachment_public_filepath \
                = mg_globals.public_store.get_unique_filepath(
                ['media_entries', unicode(media['_id']), 'attachment',
                 secure_filename(request.POST['attachment_file'].filename)])

            attachment_public_file = mg_globals.public_store.get_file(
                attachment_public_filepath, 'wb')

            try:
                attachment_public_file.write(
                    request.POST['attachment_file'].file.read())
            finally:
                request.POST['attachment_file'].file.close()

            media['attachment_files'].append(dict(
                    name=request.POST['attachment_name'] \
                        or request.POST['attachment_file'].filename,
                    filepath=attachment_public_filepath,
                    created=datetime.utcnow()
                    ))

            media.save()

            messages.add_message(
                request, messages.SUCCESS,
                "You added the attachment %s!" \
                    % (request.POST['attachment_name']
                       or request.POST['attachment_file'].filename))

            return redirect(request, 'mediagoblin.user_pages.media_home',
                            user=media.uploader()['username'],
                            media=media['slug'])
        return render_to_response(
            request,
            'mediagoblin/edit/attachments.html',
            {'media': media,
             'form': form})
    else:
        return exc.HTTPForbidden()


@require_active_login
def edit_profile(request):
    # admins may edit any user profile given a username in the querystring
    edit_username = request.GET.get('username')
    if request.user['is_admin'] and request.user['username'] != edit_username:
        user = request.db.User.find_one({'username': edit_username})
        # No need to warn again if admin just submitted an edited profile
        if request.method != 'POST':
            messages.add_message(
                request, messages.WARNING,
                _("You are editing a user's profile. Proceed with caution."))
    else:
        user = request.user

    form = forms.EditProfileForm(request.POST,
        url=user.get('url'),
        bio=user.get('bio'))

    if request.method == 'POST' and form.validate():
            user['url'] = unicode(request.POST['url'])
            user['bio'] = unicode(request.POST['bio'])

            user['bio_html'] = cleaned_markdown_conversion(user['bio'])

            user.save()

            messages.add_message(request,
                                 messages.SUCCESS,
                                 'Profile edited!')
            return redirect(request,
                           'mediagoblin.user_pages.user_home',
                            user=edit_username)

    return render_to_response(
        request,
        'mediagoblin/edit/edit_profile.html',
        {'user': user,
         'form': form})
