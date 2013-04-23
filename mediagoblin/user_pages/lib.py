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

from mediagoblin.tools.mail import send_email
from mediagoblin.tools.template import render_template
from mediagoblin.tools.translate import pass_to_ugettext as _
from mediagoblin import mg_globals
from mediagoblin.db.base import Session
from mediagoblin.db.models import CollectionItem


def send_comment_email(user, comment, media, request):
    """
    Sends comment email to user when a comment is made on their media.

    Args:
    - user: the user object to whom the email is sent
    - comment: the comment object referencing user's media
    - media: the media object the comment is about
    - request: the request
    """

    comment_url = request.urlgen(
                    'mediagoblin.user_pages.media_home.view_comment',
                    comment=comment.id,
                    user=media.get_uploader.username,
                    media=media.slug_or_id,
                    qualified=True) + '#comment'

    comment_author = comment.get_author.username

    rendered_email = render_template(
        request, 'mediagoblin/user_pages/comment_email.txt',
        {'username': user.username,
         'comment_author': comment_author,
         'comment_content': comment.content,
         'comment_url': comment_url})

    send_email(
        mg_globals.app_config['email_sender_address'],
        [user.email],
        '{instance_title} - {comment_author} '.format(
            comment_author=comment_author,
            instance_title=mg_globals.app_config['html_title']) \
                    + _('commented on your post'),
        rendered_email)


def add_media_to_collection(collection, media, note=None, commit=True):
    collection_item = CollectionItem()
    collection_item.collection = collection.id
    collection_item.media_entry = media.id
    if note:
        collection_item.note = note
    Session.add(collection_item)

    collection.items = collection.items + 1
    Session.add(collection)

    media.collected = media.collected + 1
    Session.add(media)

    if commit:
        Session.commit()
