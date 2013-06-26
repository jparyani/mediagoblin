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

from mediagoblin.db.models import Notification, \
        CommentNotification, CommentSubscription
from mediagoblin.notifications.task import email_notification_task
from mediagoblin.notifications.tools import generate_comment_message

_log = logging.getLogger(__name__)

def trigger_notification(comment, media_entry, request):
    '''
    Send out notifications about a new comment.
    '''
    subscriptions = CommentSubscription.query.filter_by(
        media_entry_id=media_entry.id).all()

    for subscription in subscriptions:
        if not subscription.notify:
            continue

        if comment.get_author == subscription.user:
            continue

        cn = CommentNotification(
            user_id=subscription.user_id,
            subject_id=comment.id)

        cn.save()

        if subscription.send_email:
            message = generate_comment_message(
                subscription.user,
                comment,
                media_entry,
                request)

            email_notification_task.apply_async([cn.id, message])


def mark_notification_seen(notification):
    if notification:
        notification.seen = True
        notification.save()


def mark_comment_notification_seen(comment_id, user):
    notification = CommentNotification.query.filter_by(
        user_id=user.id,
        subject_id=comment_id).first()

    _log.debug('Marking {0} as seen.'.format(notification))

    mark_notification_seen(notification)


def get_comment_subscription(user_id, media_entry_id):
    return CommentSubscription.query.filter_by(
        user_id=user_id,
        media_entry_id=media_entry_id).first()

def add_comment_subscription(user, media_entry):
    '''
    Create a comment subscription for a User on a MediaEntry.

    Uses the User's wants_comment_notification to set email notifications for
    the subscription to enabled/disabled.
    '''
    cn = get_comment_subscription(user.id, media_entry.id)

    if not cn:
        cn = CommentSubscription(
            user_id=user.id,
            media_entry_id=media_entry.id)

    cn.notify = True

    if not user.wants_comment_notification:
        cn.send_email = False

    cn.save()


def silence_comment_subscription(user, media_entry):
    '''
    Silence a subscription so that the user is never notified in any way about
    new comments on an entry
    '''
    cn = get_comment_subscription(user.id, media_entry.id)

    if cn:
        cn.notify = False
        cn.send_email = False
        cn.save()


def remove_comment_subscription(user, media_entry):
    cn = get_comment_subscription(user.id, media_entry.id)

    if cn:
        cn.delete()


NOTIFICATION_FETCH_LIMIT = 100


def get_notifications(user_id, only_unseen=True):
    query = Notification.query.filter_by(user_id=user_id)

    if only_unseen:
        query = query.filter_by(seen=False)

    notifications = query.limit(
        NOTIFICATION_FETCH_LIMIT).all()

    return notifications

def get_notification_count(user_id, only_unseen=True):
    query = Notification.query.filter_by(user_id=user_id)

    if only_unseen:
        query = query.filter_by(seen=False)

    count = query.count()

    return count
