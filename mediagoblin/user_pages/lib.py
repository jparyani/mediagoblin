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
from mediagoblin import mg_globals

def send_comment_email(user, comment, media, request):
    """
    Sends comment email to user when a comment is made on their media.

    Args:
    - user: the user object to whom the email is sent
    - comment: the comment object referencing user's media
    - media: the media object the comment is about
    - request: the request
    """

    comment_url = u'http://{host}{comment_uri}'.format( 
            host=request.host,
            comment_uri=request.urlgen(
                'mediagoblin.user_pages.media_home.view_comment',
                comment = comment._id,
                user = media.get_uploader.username,
                media = media.slug_or_id) + '#comment')

    comment_author = comment.get_author['username']

    rendered_email = render_template(
        request, 'mediagoblin/user_pages/comment_email.txt',
        {'username':user.username,
         'comment_author':comment_author,
         'comment_content':comment.content,
         'comment_url':comment_url})

    send_email(
        mg_globals.app_config['email_sender_address'],
        [user.email],
        'GNU MediaGoblin - {comment_author} commented on your post'.format(
            comment_author=comment_author),
        rendered_email)
