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

from mediagoblin.tests.tools import (fixture_add_user,
            fixture_add_comment_report, fixture_add_comment)
from mediagoblin.db.models import User, CommentReport, MediaComment, UserBan
from mediagoblin.tools import template, mail
from webtest import AppError

class TestModerationViews:
    @pytest.fixture(autouse=True)
    def _setup(self, test_app):
        self.test_app = test_app

        fixture_add_user(u'admin',
            privileges=[u'admin',u'active'])
        fixture_add_user(u'moderator',
            privileges=[u'moderator',u'active'])
        fixture_add_user(u'regular',
            privileges=[u'active',u'commenter'])
        self.query_for_users()

    def login(self, username):
        self.test_app.post(
            '/auth/login/', {
                'username': username,
                'password': 'toast'})
        self.query_for_users()

    def logout(self):
        self.test_app.get('/auth/logout/')
        self.query_for_users()

    def query_for_users(self):
        self.admin_user = User.query.filter(User.username==u'admin').first()
        self.mod_user = User.query.filter(User.username==u'moderator').first()
        self.user = User.query.filter(User.username==u'regular').first()

    def do_post(self, data, *context_keys, **kwargs):
        url = kwargs.pop('url', '/submit/')
        do_follow = kwargs.pop('do_follow', False)
        template.clear_test_template_context()
        response = self.test_app.post(url, data, **kwargs)
        if do_follow:
            response.follow()
        context_data = template.TEMPLATE_TEST_CONTEXT
        for key in context_keys:
            context_data = context_data[key]
        return response, context_data

    def testGiveOrTakeAwayPrivileges(self):
        self.login(u'admin')
        # First, test an admin taking away a privilege from a user
        #----------------------------------------------------------------------
        response, context = self.do_post({'privilege_name':u'commenter'},
            url='/mod/users/{0}/privilege/'.format(self.user.username))
        assert response.status == '302 FOUND'
        self.query_for_users()
        assert not self.user.has_privilege(u'commenter')

        # Then, test an admin giving a privilege to a user
        #----------------------------------------------------------------------
        response, context = self.do_post({'privilege_name':u'commenter'},
            url='/mod/users/{0}/privilege/'.format(self.user.username))
        assert response.status == '302 FOUND'
        self.query_for_users()
        assert self.user.has_privilege(u'commenter')

        # Then, test a mod trying to take away a privilege from a user
        # they are not allowed to do this, so this will raise an error
        #----------------------------------------------------------------------
        self.logout()
        self.login(u'moderator')

        with pytest.raises(AppError) as excinfo:
            response, context = self.do_post({'privilege_name':u'commenter'},
                url='/mod/users/{0}/privilege/'.format(self.user.username))
        assert 'Bad response: 403 FORBIDDEN' in str(excinfo)
        self.query_for_users()

        assert self.user.has_privilege(u'commenter')

    def testReportResolution(self):
        self.login(u'moderator')

        # First, test a moderators taking away a user's privilege in response
        # to a reported comment
        #----------------------------------------------------------------------
        fixture_add_comment_report(reported_user=self.user)
        comment_report = CommentReport.query.filter(
            CommentReport.reported_user==self.user).first()

        response = self.test_app.get('/mod/reports/{0}/'.format(
            comment_report.id))
        assert response.status == '200 OK'
        self.query_for_users()
        comment_report = CommentReport.query.filter(
            CommentReport.reported_user==self.user).first()

        response, context = self.do_post({'action_to_resolve':[u'takeaway'],
            'take_away_privileges':[u'commenter'],
            'targeted_user':self.user.id},
            url='/mod/reports/{0}/'.format(comment_report.id))

        self.query_for_users()
        comment_report = CommentReport.query.filter(
            CommentReport.reported_user==self.user).first()
        assert response.status == '302 FOUND'
        assert not self.user.has_privilege(u'commenter')
        assert comment_report.is_archived_report() is True

        fixture_add_comment_report(reported_user=self.user)
        comment_report = CommentReport.query.filter(
            CommentReport.reported_user==self.user).first()

        # Then, test a moderator sending an email to a user in response to a
        # reported comment
        #----------------------------------------------------------------------
        self.query_for_users()

        response, context = self.do_post({'action_to_resolve':[u'sendmessage'],
            'message_to_user':'This is your last warning, regular....',
            'targeted_user':self.user.id},
            url='/mod/reports/{0}/'.format(comment_report.id))

        self.query_for_users()
        comment_report = CommentReport.query.filter(
            CommentReport.reported_user==self.user).first()
        assert response.status == '302 FOUND'
        assert mail.EMAIL_TEST_MBOX_INBOX ==  [{'to': [u'regular@example.com'],
            'message': 'Content-Type: text/plain; charset="utf-8"\n\
MIME-Version: 1.0\nContent-Transfer-Encoding: base64\nSubject: Warning from- \
moderator \nFrom: notice@mediagoblin.example.org\nTo: regular@example.com\n\n\
VGhpcyBpcyB5b3VyIGxhc3Qgd2FybmluZywgcmVndWxhci4uLi4=\n',
            'from': 'notice@mediagoblin.example.org'}]
        assert comment_report.is_archived_report() is True

        # Then test a moderator banning a user AND a moderator deleting the
        # offending comment. This also serves as a test for taking multiple
        # actions to resolve a report
        #----------------------------------------------------------------------
        self.query_for_users()
        fixture_add_comment(author=self.user.id,
            comment=u'Comment will be removed')
        test_comment = MediaComment.query.filter(
            MediaComment.author==self.user.id).first()
        fixture_add_comment_report(comment=test_comment,
            reported_user=self.user)
        comment_report = CommentReport.query.filter(
            CommentReport.comment==test_comment).filter(
            CommentReport.resolved==None).first()

        response, context = self.do_post(
            {'action_to_resolve':[u'userban', u'delete'],
            'targeted_user':self.user.id,
            'why_user_was_banned':u'',
            'user_banned_until':u''},
            url='/mod/reports/{0}/'.format(comment_report.id))
        assert response.status == '302 FOUND'
        self.query_for_users()
        test_user_ban = UserBan.query.filter(
            UserBan.user_id == self.user.id).first()
        assert test_user_ban is not None
        test_comment = MediaComment.query.filter(
            MediaComment.author==self.user.id).first()
        assert test_comment is None

        # Then, test what happens when a moderator attempts to punish an admin
        # from a reported comment on an admin.
        #----------------------------------------------------------------------
        fixture_add_comment_report(reported_user=self.admin_user)
        comment_report = CommentReport.query.filter(
            CommentReport.reported_user==self.admin_user).filter(
            CommentReport.resolved==None).first()

        response, context = self.do_post({'action_to_resolve':[u'takeaway'],
            'take_away_privileges':[u'active'],
            'targeted_user':self.admin_user.id},
            url='/mod/reports/{0}/'.format(comment_report.id))
        self.query_for_users()

        assert response.status == '200 OK'
        assert self.admin_user.has_privilege(u'active')

    def testAllModerationViews(self):
        self.login(u'moderator')
        username = self.user.username
        self.query_for_users()
        fixture_add_comment_report(reported_user=self.admin_user)
        response = self.test_app.get('/mod/reports/')
        assert response.status == "200 OK"

        response = self.test_app.get('/mod/reports/1/')
        assert response.status == "200 OK"

        response = self.test_app.get('/mod/users/')
        assert response.status == "200 OK"

        user_page_url = '/mod/users/{0}/'.format(username)
        response = self.test_app.get(user_page_url)
        assert response.status == "200 OK"

        self.test_app.get('/mod/media/')
        assert response.status == "200 OK"

    def testBanUnBanUser(self):
        self.login(u'admin')
        username = self.user.username
        user_id = self.user.id
        ban_url = '/mod/users/{0}/ban/'.format(username)
        response, context = self.do_post({
            'user_banned_until':u'',
            'why_user_was_banned':u'Because I said so'},
            url=ban_url)

        assert response.status == "302 FOUND"
        user_banned = UserBan.query.filter(UserBan.user_id==user_id).first()
        assert user_banned is not None
        assert user_banned.expiration_date is None
        assert user_banned.reason == u'Because I said so'

        response, context = self.do_post({},
            url=ban_url)

        assert response.status == "302 FOUND"
        user_banned = UserBan.query.filter(UserBan.user_id==user_id).first()
        assert user_banned is None
