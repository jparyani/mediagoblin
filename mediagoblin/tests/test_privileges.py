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

import six
import pytest
from datetime import date, timedelta
from webtest import AppError

from mediagoblin.tests.tools import fixture_add_user, fixture_media_entry

from mediagoblin.db.models import User, UserBan
from mediagoblin.tools import template

from .resources import GOOD_JPG

class TestPrivilegeFunctionality:

    @pytest.fixture(autouse=True)
    def _setup(self, test_app):
        self.test_app = test_app

        fixture_add_user(u'alex',
            privileges=[u'admin',u'active'])
        fixture_add_user(u'meow',
            privileges=[u'moderator',u'active',u'reporter'])
        fixture_add_user(u'natalie',
            privileges=[u'active'])
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

    def query_for_users(self):
        self.admin_user = User.query.filter(User.username==u'alex').first()
        self.mod_user = User.query.filter(User.username==u'meow').first()
        self.user = User.query.filter(User.username==u'natalie').first()

    def testUserBanned(self):
        self.login(u'natalie')
        uid = self.user.id
        # First, test what happens when a user is banned indefinitely
        #----------------------------------------------------------------------
        user_ban = UserBan(user_id=uid,
            reason=u'Testing whether user is banned',
            expiration_date=None)
        user_ban.save()

        response = self.test_app.get('/')
        assert response.status == "200 OK"
        assert b"You are Banned" in response.body
        # Then test what happens when that ban has an expiration date which
        # hasn't happened yet
        #----------------------------------------------------------------------
        user_ban = UserBan.query.get(uid)
        user_ban.delete()
        user_ban = UserBan(user_id=uid,
            reason=u'Testing whether user is banned',
            expiration_date= date.today() + timedelta(days=20))
        user_ban.save()

        response = self.test_app.get('/')
        assert response.status == "200 OK"
        assert b"You are Banned" in response.body

        # Then test what happens when that ban has an expiration date which
        # has already happened
        #----------------------------------------------------------------------
        user_ban = UserBan.query.get(uid)
        user_ban.delete()
        exp_date = date.today() - timedelta(days=20)
        user_ban = UserBan(user_id=uid,
            reason=u'Testing whether user is banned',
            expiration_date= exp_date)
        user_ban.save()

        response = self.test_app.get('/')
        assert response.status == "302 FOUND"
        assert not b"You are Banned" in response.body

    def testVariousPrivileges(self):
        # The various actions that require privileges (ex. reporting,
        # commenting, moderating...) are tested in other tests. This method
        # will be used to ensure that those actions are impossible for someone
        # without the proper privileges.
        # For other tests that show what happens when a user has the proper
        # privileges, check out:
        #       tests/test_moderation.py                moderator
        #       tests/test_notifications.py             commenter
        #       tests/test_reporting.py                 reporter
        #       tests/test_submission.py                uploader
        #----------------------------------------------------------------------
        self.login(u'natalie')

        # First test the get and post requests of submission/uploading
        #----------------------------------------------------------------------
        with pytest.raises(AppError) as excinfo:
            response = self.test_app.get('/submit/')
        excinfo = str(excinfo) if six.PY2 else str(excinfo).encode('ascii')
        assert b'Bad response: 403 FORBIDDEN' in excinfo


        with pytest.raises(AppError) as excinfo:
            response = self.do_post({'upload_files':[('file',GOOD_JPG)],
                'title':u'Normal Upload 1'},
                url='/submit/')
        excinfo = str(excinfo) if six.PY2 else str(excinfo).encode('ascii')
        assert b'Bad response: 403 FORBIDDEN' in excinfo

        # Test that a user cannot comment without the commenter privilege
        #----------------------------------------------------------------------
        self.query_for_users()

        media_entry = fixture_media_entry(uploader=self.admin_user.id,
            state=u'processed')

        media_entry_id = media_entry.id
        media_uri_id = '/u/{0}/m/{1}/'.format(self.admin_user.username,
                                              media_entry.id)
        media_uri_slug = '/u/{0}/m/{1}/'.format(self.admin_user.username,
                                                media_entry.slug)
        response = self.test_app.get(media_uri_slug)
        assert not b"Add a comment" in response.body

        self.query_for_users()
        with pytest.raises(AppError) as excinfo:
            response = self.test_app.post(
                media_uri_id + 'comment/add/',
                {'comment_content': u'Test comment #42'})
        excinfo = str(excinfo) if six.PY2 else str(excinfo).encode('ascii')
        assert b'Bad response: 403 FORBIDDEN' in excinfo

        # Test that a user cannot report without the reporter privilege
        #----------------------------------------------------------------------
        with pytest.raises(AppError) as excinfo:
            response = self.test_app.get(media_uri_slug+"report/")
        excinfo = str(excinfo) if six.PY2 else str(excinfo).encode('ascii')
        assert b'Bad response: 403 FORBIDDEN' in excinfo

        with pytest.raises(AppError) as excinfo:
            response = self.do_post(
                {'report_reason':u'Testing Reports #1',
                'reporter_id':u'3'},
                url=(media_uri_slug+"report/"))
        excinfo = str(excinfo) if six.PY2 else str(excinfo).encode('ascii')
        assert b'Bad response: 403 FORBIDDEN' in excinfo

        # Test that a user cannot access the moderation pages w/o moderator
        # or admin privileges
        #----------------------------------------------------------------------
        with pytest.raises(AppError) as excinfo:
            response = self.test_app.get("/mod/users/")
        excinfo = str(excinfo) if six.PY2 else str(excinfo).encode('ascii')
        assert b'Bad response: 403 FORBIDDEN' in excinfo

        with pytest.raises(AppError) as excinfo:
            response = self.test_app.get("/mod/reports/")
        excinfo = str(excinfo) if six.PY2 else str(excinfo).encode('ascii')
        assert b'Bad response: 403 FORBIDDEN' in excinfo

        with pytest.raises(AppError) as excinfo:
            response = self.test_app.get("/mod/media/")
        excinfo = str(excinfo) if six.PY2 else str(excinfo).encode('ascii')
        assert b'Bad response: 403 FORBIDDEN' in excinfo

        with pytest.raises(AppError) as excinfo:
            response = self.test_app.get("/mod/users/1/")
        excinfo = str(excinfo) if six.PY2 else str(excinfo).encode('ascii')
        assert b'Bad response: 403 FORBIDDEN' in excinfo

        with pytest.raises(AppError) as excinfo:
            response = self.test_app.get("/mod/reports/1/")
        excinfo = str(excinfo) if six.PY2 else str(excinfo).encode('ascii')
        assert b'Bad response: 403 FORBIDDEN' in excinfo

        self.query_for_users()

        with pytest.raises(AppError) as excinfo:
            response, context = self.do_post({'action_to_resolve':[u'takeaway'],
                'take_away_privileges':[u'active'],
                'targeted_user':self.admin_user.id},
                url='/mod/reports/1/')
            self.query_for_users()
        excinfo = str(excinfo) if six.PY2 else str(excinfo).encode('ascii')
        assert b'Bad response: 403 FORBIDDEN' in excinfo
