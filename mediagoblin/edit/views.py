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

from datetime import datetime

from werkzeug.exceptions import Forbidden
from werkzeug.utils import secure_filename

from mediagoblin import messages
from mediagoblin import mg_globals

from mediagoblin.auth import lib as auth_lib
from mediagoblin.edit import forms
from mediagoblin.edit.lib import may_edit_media
from mediagoblin.decorators import (require_active_login, active_user_from_url,
     get_media_entry_by_id,
     user_may_alter_collection, get_user_collection)
from mediagoblin.tools.response import render_to_response, redirect
from mediagoblin.tools.translate import pass_to_ugettext as _
from mediagoblin.tools.text import (
    convert_to_tag_list_of_dicts, media_tags_as_string)
from mediagoblin.tools.url import slugify
from mediagoblin.db.util import check_media_slug_used, check_collection_slug_used

import mimetypes


@get_media_entry_by_id
@require_active_login
def edit_media(request, media):
    if not may_edit_media(request, media):
        raise Forbidden("User may not edit this media")

    defaults = dict(
        title=media.title,
        slug=media.slug,
        description=media.description,
        tags=media_tags_as_string(media.tags),
        license=media.license)

    form = forms.EditForm(
        request.form,
        **defaults)

    if request.method == 'POST' and form.validate():
        # Make sure there isn't already a MediaEntry with such a slug
        # and userid.
        slug = slugify(form.slug.data)
        slug_used = check_media_slug_used(media.uploader, slug, media.id)

        if slug_used:
            form.slug.errors.append(
                _(u'An entry with that slug already exists for this user.'))
        else:
            media.title = form.title.data
            media.description = form.description.data
            media.tags = convert_to_tag_list_of_dicts(
                                   form.tags.data)

            media.license = unicode(form.license.data) or None
            media.slug = slug
            media.save()

            return redirect(request,
                            location=media.url_for_self(request.urlgen))

    if request.user.is_admin \
            and media.uploader != request.user.id \
            and request.method != 'POST':
        messages.add_message(
            request, messages.WARNING,
            _("You are editing another user's media. Proceed with caution."))

    return render_to_response(
        request,
        'mediagoblin/edit/edit.html',
        {'media': media,
         'form': form})


# Mimetypes that browsers parse scripts in.
# Content-sniffing isn't taken into consideration.
UNSAFE_MIMETYPES = [
        'text/html',
        'text/svg+xml']


@get_media_entry_by_id
@require_active_login
def edit_attachments(request, media):
    if mg_globals.app_config['allow_attachments']:
        form = forms.EditAttachmentsForm()

        # Add any attachements
        if 'attachment_file' in request.files \
            and request.files['attachment_file']:

            # Security measure to prevent attachments from being served as
            # text/html, which will be parsed by web clients and pose an XSS
            # threat.
            #
            # TODO
            # This method isn't flawless as some browsers may perform
            # content-sniffing.
            # This method isn't flawless as we do the mimetype lookup on the
            # machine parsing the upload form, and not necessarily the machine
            # serving the attachments.
            if mimetypes.guess_type(
                    request.files['attachment_file'].filename)[0] in \
                    UNSAFE_MIMETYPES:
                public_filename = secure_filename('{0}.notsafe'.format(
                    request.files['attachment_file'].filename))
            else:
                public_filename = secure_filename(
                        request.files['attachment_file'].filename)

            attachment_public_filepath \
                = mg_globals.public_store.get_unique_filepath(
                ['media_entries', unicode(media.id), 'attachment',
                 public_filename])

            attachment_public_file = mg_globals.public_store.get_file(
                attachment_public_filepath, 'wb')

            try:
                attachment_public_file.write(
                    request.files['attachment_file'].stream.read())
            finally:
                request.files['attachment_file'].stream.close()

            media.attachment_files.append(dict(
                    name=form.attachment_name.data \
                        or request.files['attachment_file'].filename,
                    filepath=attachment_public_filepath,
                    created=datetime.utcnow(),
                    ))

            media.save()

            messages.add_message(
                request, messages.SUCCESS,
                _("You added the attachment %s!") \
                    % (form.attachment_name.data
                       or request.files['attachment_file'].filename))

            return redirect(request,
                            location=media.url_for_self(request.urlgen))
        return render_to_response(
            request,
            'mediagoblin/edit/attachments.html',
            {'media': media,
             'form': form})
    else:
        raise Forbidden("Attachments are disabled")

@require_active_login
def legacy_edit_profile(request):
    """redirect the old /edit/profile/?username=USER to /u/USER/edit/"""
    username = request.GET.get('username') or request.user.username
    return redirect(request, 'mediagoblin.edit.profile', user=username)


@require_active_login
@active_user_from_url
def edit_profile(request, url_user=None):
    # admins may edit any user profile
    if request.user.username != url_user.username:
        if not request.user.is_admin:
            raise Forbidden(_("You can only edit your own profile."))

        # No need to warn again if admin just submitted an edited profile
        if request.method != 'POST':
            messages.add_message(
                request, messages.WARNING,
                _("You are editing a user's profile. Proceed with caution."))

    user = url_user

    form = forms.EditProfileForm(request.form,
        url=user.url,
        bio=user.bio)

    if request.method == 'POST' and form.validate():
        user.url = unicode(form.url.data)
        user.bio = unicode(form.bio.data)

        user.save()

        messages.add_message(request,
                             messages.SUCCESS,
                             _("Profile changes saved"))
        return redirect(request,
                       'mediagoblin.user_pages.user_home',
                        user=user.username)

    return render_to_response(
        request,
        'mediagoblin/edit/edit_profile.html',
        {'user': user,
         'form': form})


@require_active_login
def edit_account(request):
    user = request.user
    form = forms.EditAccountForm(request.form,
        wants_comment_notification=user.wants_comment_notification,
        license_preference=user.license_preference)

    if request.method == 'POST':
        form_validated = form.validate()

        if form_validated and \
                form.wants_comment_notification.validate(form):
            user.wants_comment_notification = \
                form.wants_comment_notification.data

        if form_validated and \
                form.new_password.data or form.old_password.data:
            password_matches = auth_lib.bcrypt_check_password(
                form.old_password.data,
                user.pw_hash)
            if password_matches:
                #the entire form validates and the password matches
                user.pw_hash = auth_lib.bcrypt_gen_password_hash(
                    form.new_password.data)
            else:
                form.old_password.errors.append(_('Wrong password'))

        if form_validated and \
                form.license_preference.validate(form):
            user.license_preference = \
                form.license_preference.data

        if form_validated and not form.errors:
            user.save()
            messages.add_message(request,
                messages.SUCCESS,
                _("Account settings saved"))
            return redirect(request,
                'mediagoblin.user_pages.user_home',
                user=user.username)

    return render_to_response(
        request,
        'mediagoblin/edit/edit_account.html',
        {'user': user,
         'form': form})


@require_active_login
def delete_account(request):
    """Delete a user completely"""
    user = request.user
    if request.method == 'POST':
        if request.form.get(u'confirmed'):
            # Form submitted and confirmed. Actually delete the user account
            # Log out user and delete cookies etc.
            # TODO: Should we be using MG.auth.views.py:logout for this?
            request.session.delete()

            # Delete user account and all related media files etc....
            request.user.delete()

            # We should send a message that the user has been deleted
            # successfully. But we just deleted the session, so we
            # can't...
            return redirect(request, 'index')

        else: # Did not check the confirmation box...
            messages.add_message(
                request, messages.WARNING,
                _('You need to confirm the deletion of your account.'))

    # No POST submission or not confirmed, just show page
    return render_to_response(
        request,
        'mediagoblin/edit/delete_account.html',
        {'user': user})


@require_active_login
@user_may_alter_collection
@get_user_collection
def edit_collection(request, collection):
    defaults = dict(
        title=collection.title,
        slug=collection.slug,
        description=collection.description)

    form = forms.EditCollectionForm(
        request.form,
        **defaults)

    if request.method == 'POST' and form.validate():
        # Make sure there isn't already a Collection with such a slug
        # and userid.
        slug_used = check_collection_slug_used(collection.creator,
                form.slug.data, collection.id)

        # Make sure there isn't already a Collection with this title
        existing_collection = request.db.Collection.find_one({
                'creator': request.user.id,
                'title':form.title.data})

        if existing_collection and existing_collection.id != collection.id:
            messages.add_message(
                request, messages.ERROR,
                _('You already have a collection called "%s"!') % \
                    form.title.data)
        elif slug_used:
            form.slug.errors.append(
                _(u'A collection with that slug already exists for this user.'))
        else:
            collection.title = unicode(form.title.data)
            collection.description = unicode(form.description.data)
            collection.slug = unicode(form.slug.data)

            collection.save()

            return redirect(request, "mediagoblin.user_pages.user_collection",
                            user=collection.get_creator.username,
                            collection=collection.slug)

    if request.user.is_admin \
            and collection.creator != request.user.id \
            and request.method != 'POST':
        messages.add_message(
            request, messages.WARNING,
            _("You are editing another user's collection. Proceed with caution."))

    return render_to_response(
        request,
        'mediagoblin/edit/edit_collection.html',
        {'collection': collection,
         'form': form})
