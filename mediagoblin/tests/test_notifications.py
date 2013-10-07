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

import pytest

import urlparse

from mediagoblin.tools import template, mail

from mediagoblin.db.models import Notification, CommentNotification, \
        CommentSubscription
from mediagoblin.db.base import Session

from mediagoblin.notifications import mark_comment_notification_seen

from mediagoblin.tests.tools import fixture_add_comment, \
    fixture_media_entry, fixture_add_user, \
    fixture_comment_subscription


class TestNotifications:
    @pytest.fixture(autouse=True)
    def setup(self, test_app):
        self.test_app = test_app

        # TODO: Possibly abstract into a decorator like:
        # @as_authenticated_user('chris')
        self.test_user = fixture_add_user(privileges=[u'active',u'commenter'])

        self.current_user = None

        self.login()

    def login(self, username=u'chris', password=u'toast'):
        response = self.test_app.post(
            '/auth/login/', {
                'username': username,
                'password': password})

        response.follow()

        assert urlparse.urlsplit(response.location)[2] == '/'
        assert 'mediagoblin/root.html' in template.TEMPLATE_TEST_CONTEXT

        ctx = template.TEMPLATE_TEST_CONTEXT['mediagoblin/root.html']

        assert Session.merge(ctx['request'].user).username == username

        self.current_user = ctx['request'].user

    def logout(self):
        self.test_app.get('/auth/logout/')
        self.current_user = None

    @pytest.mark.parametrize('wants_email', [True, False])
    def test_comment_notification(self, wants_email):
        '''
        Test
        - if a notification is created when posting a comment on
          another users media entry.
        - that the comment data is consistent and exists.

        '''
        user = fixture_add_user('otherperson', password='nosreprehto',
                                wants_comment_notification=wants_email,
                                privileges=[u'active',u'commenter'])

        assert user.wants_comment_notification == wants_email

        user_id = user.id

        media_entry = fixture_media_entry(uploader=user.id, state=u'processed')

        media_entry_id = media_entry.id

        subscription = fixture_comment_subscription(media_entry)

        subscription_id = subscription.id

        media_uri_id = '/u/{0}/m/{1}/'.format(user.username,
                                              media_entry.id)
        media_uri_slug = '/u/{0}/m/{1}/'.format(user.username,
                                                media_entry.slug)

        self.test_app.post(
            media_uri_id + 'comment/add/',
            {
                'comment_content': u'Test comment #42'
            }
        )

        notifications = Notification.query.filter_by(
            user_id=user.id).all()

        assert len(notifications) == 1

        notification = notifications[0]

        assert type(notification) == CommentNotification
        assert notification.seen == False
        assert notification.user_id == user.id
        assert notification.subject.get_author.id == self.test_user.id
        assert notification.subject.content == u'Test comment #42'

        if wants_email == True:
            assert mail.EMAIL_TEST_MBOX_INBOX == [
                {'from': 'notice@mediagoblin.example.org',
                'message': 'Content-Type: text/plain; \
charset="utf-8"\nMIME-Version: 1.0\nContent-Transfer-Encoding: \
base64\nSubject: GNU MediaGoblin - chris commented on your \
post\nFrom: notice@mediagoblin.example.org\nTo: \
otherperson@example.com\n\nSGkgb3RoZXJwZXJzb24sCmNocmlzIGNvbW1lbnRlZCBvbiB5b3VyIHBvc3QgKGh0dHA6Ly9sb2Nh\nbGhvc3Q6ODAvdS9vdGhlcnBlcnNvbi9tL3NvbWUtdGl0bGUvYy8xLyNjb21tZW50KSBhdCBHTlUg\nTWVkaWFHb2JsaW4KClRlc3QgY29tbWVudCAjNDIKCkdOVSBNZWRpYUdvYmxpbg==\n',
                'to': [u'otherperson@example.com']}]
        else:
            assert mail.EMAIL_TEST_MBOX_INBOX == []


        # Save the ids temporarily because of DetachedInstanceError
        notification_id = notification.id
        comment_id = notification.subject.id

        self.logout()
        self.login('otherperson', 'nosreprehto')

        self.test_app.get(media_uri_slug + '/c/{0}/'.format(comment_id))

        notification = Notification.query.filter_by(id=notification_id).first()

        assert notification.seen == True

        self.test_app.get(media_uri_slug + '/notifications/silence/')

        subscription = CommentSubscription.query.filter_by(id=subscription_id)\
                .first()

        assert subscription.notify == False

        notifications = Notification.query.filter_by(
            user_id=user_id).all()

        # User should not have been notified
        assert len(notifications) == 1

    def test_mark_all_comment_notifications_seen(self):
        """ Test that mark_all_comments_seen works"""

        user = fixture_add_user('otherperson', password='nosreprehto',
                        privileges=[u'active'])

        media_entry = fixture_media_entry(uploader=user.id, state=u'processed')

        fixture_comment_subscription(media_entry)

        media_uri_id = '/u/{0}/m/{1}/'.format(user.username,
                                              media_entry.id)

        # add 2 comments
        self.test_app.post(
            media_uri_id + 'comment/add/',
            {
                'comment_content': u'Test comment #43'
            }
        )

        self.test_app.post(
            media_uri_id + 'comment/add/',
            {
                'comment_content': u'Test comment #44'
            }
        )

        notifications = Notification.query.filter_by(
            user_id=user.id).all()

        assert len(notifications) == 2

        # both comments should not be marked seen
        assert notifications[0].seen == False
        assert notifications[1].seen == False

        # login with other user to mark notifications seen
        self.logout()
        self.login('otherperson', 'nosreprehto')

        # mark all comment notifications seen
        res = self.test_app.get('/notifications/comments/mark_all_seen/')
        res.follow()

        assert urlparse.urlsplit(res.location)[2] == '/'

        notifications = Notification.query.filter_by(
            user_id=user.id).all()

        # both notifications should be marked seen
        assert notifications[0].seen == True
        assert notifications[1].seen == True
