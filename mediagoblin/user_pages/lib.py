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

from mediagoblin import mg_globals
from mediagoblin.db.base import Session
from mediagoblin.db.models import (CollectionItem, MediaReport, CommentReport,
                                   MediaComment, MediaEntry)
from mediagoblin.tools.mail import send_email
from mediagoblin.tools.pluginapi import hook_runall
from mediagoblin.tools.template import render_template
from mediagoblin.tools.translate import pass_to_ugettext as _


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
    Session.add(media)

    hook_runall('collection_add_media', collection_item=collection_item)

    if commit:
        Session.commit()


def build_report_object(report_form, media_entry=None, comment=None):
    """
    This function is used to convert a form object (from a User filing a
        report) into either a MediaReport or CommentReport object.

    :param report_form          A MediaReportForm or a CommentReportForm object
                                  with valid information from a POST request.
    :param media_entry          A MediaEntry object. The MediaEntry being repo-
                                  -rted by a MediaReport. In a CommentReport,
                                  this will be None.
    :param comment              A MediaComment object. The MediaComment being
                                  reported by a CommentReport. In a MediaReport
                                  this will be None.

    :returns                A MediaReport object if a valid MediaReportForm is
                              passed as kwarg media_entry. This MediaReport has
                              not been saved.
    :returns                A CommentReport object if a valid CommentReportForm
                              is passed as kwarg comment. This CommentReport
                              has not been saved.
    :returns                None if the form_dict is invalid.
    """

    if report_form.validate() and comment is not None:
        report_object = CommentReport()
        report_object.comment_id = comment.id
        report_object.reported_user_id = MediaComment.query.get(
            comment.id).get_author.id
    elif report_form.validate() and media_entry is not None:
        report_object = MediaReport()
        report_object.media_entry_id = media_entry.id
        report_object.reported_user_id = MediaEntry.query.get(
            media_entry.id).get_uploader.id
    else:
        return None

    report_object.report_content = report_form.report_reason.data
    report_object.reporter_id = report_form.reporter_id.data
    return report_object
