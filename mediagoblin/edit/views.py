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
from string import split

from mediagoblin import messages
from mediagoblin.util import render_to_response, redirect, clean_html, \
                             TAGS_DELIMITER
from mediagoblin.edit import forms
from mediagoblin.edit.lib import may_edit_media
from mediagoblin.decorators import require_active_login, get_user_media_entry

import markdown


@get_user_media_entry
@require_active_login
def edit_media(request, media):
    if not may_edit_media(request, media):
        return exc.HTTPForbidden()

    form = forms.EditForm(request.POST,
        title = media['title'],
        slug = media['slug'],
        description = media['description'],
        tags = TAGS_DELIMITER.join(media['tags']))

    if request.method == 'POST' and form.validate():
        # Make sure there isn't already a MediaEntry with such a slug
        # and userid.
        existing_user_slug_entries = request.db.MediaEntry.find(
            {'slug': request.POST['slug'],
             'uploader': media['uploader'],
             '_id': {'$ne': media['_id']}}).count()
        
        if existing_user_slug_entries:
            form.slug.errors.append(
                u'An entry with that slug already exists for this user.')
        else:
            media['title'] = request.POST['title']
            media['description'] = request.POST.get('description')
            
            md = markdown.Markdown(
                safe_mode = 'escape')
            media['description_html'] = clean_html(
                md.convert(
                    media['description']))

            media['slug'] = request.POST['slug']
            media['tags'] = split(request.POST['tags'])
            media.save()

            return redirect(request, "mediagoblin.user_pages.media_home",
                user=media.uploader()['username'], media=media['slug'])

    if request.user['is_admin'] \
            and media['uploader'] != request.user['_id'] \
            and request.method != 'POST':
        messages.add_message(
            request, messages.WARNING,
            "You are editing another user's media. Proceed with caution.")
        

    return render_to_response(
        request,
        'mediagoblin/edit/edit.html',
        {'media': media,
         'form': form})
    

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
                "You are editing a user's profile. Proceed with caution.")
    else:
        user = request.user

    form = forms.EditProfileForm(request.POST,
        url = user.get('url'),
        bio = user.get('bio'))

    if request.method == 'POST' and form.validate():
            user['url'] = request.POST['url']
            user['bio'] = request.POST['bio']
            user.save()

            messages.add_message(request, 
            	                 messages.SUCCESS, 
            	                 'Profile edited!')
            return redirect(request,
                           'mediagoblin.user_pages.user_home',
            	            username=edit_username)

    return render_to_response(
        request,
        'mediagoblin/edit/edit_profile.html',
        {'user': user,
         'form': form})
