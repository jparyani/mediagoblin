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

import urlparse

from mediagoblin import mg_globals
from mediagoblin.db.models import User
from mediagoblin.tests.tools import fixture_add_user
from mediagoblin import auth
from mediagoblin.tools import template, mail


class TestUserEdit(object):
    def setup(self):
        # set up new user
        self.user_password = u'toast'
        self.user = fixture_add_user(password = self.user_password)

    def login(self, test_app):
        test_app.post(
            '/auth/login/', {
                'username': self.user.username,
                'password': self.user_password})


    def test_user_deletion(self, test_app):
        """Delete user via web interface"""
        self.login(test_app)

        # Make sure user exists
        assert User.query.filter_by(username=u'chris').first()

        res = test_app.post('/edit/account/delete/', {'confirmed': 'y'})

        # Make sure user has been deleted
        assert User.query.filter_by(username=u'chris').first() == None

        #TODO: make sure all corresponding items comments etc have been
        # deleted too. Perhaps in submission test?

        #Restore user at end of test
        self.user = fixture_add_user(password = self.user_password)
        self.login(test_app)


    def test_change_password(self, test_app):
        """Test changing password correctly and incorrectly"""
        self.login(test_app)

        # test that the password can be changed
        template.clear_test_template_context()
        res = test_app.post(
            '/edit/password/', {
                'old_password': 'toast',
                'new_password': '123456',
                })
        res.follow()

        # Did we redirect to the correct page?
        assert urlparse.urlsplit(res.location)[2] == '/edit/account/'

        # test_user has to be fetched again in order to have the current values
        test_user = User.query.filter_by(username=u'chris').first()
        assert auth.check_password('123456', test_user.pw_hash)
        # Update current user passwd
        self.user_password = '123456'

        # test that the password cannot be changed if the given
        # old_password is wrong
        template.clear_test_template_context()
        test_app.post(
            '/edit/password/', {
                'old_password': 'toast',
                'new_password': '098765',
                })

        test_user = User.query.filter_by(username=u'chris').first()
        assert not auth.check_password('098765', test_user.pw_hash)


    def test_change_bio_url(self, test_app):
        """Test changing bio and URL"""
        self.login(test_app)

        # Test if legacy profile editing URL redirects correctly
        res = test_app.post(
            '/edit/profile/', {
                'bio': u'I love toast!',
                'url': u'http://dustycloud.org/'}, expect_errors=True)

        # Should redirect to /u/chris/edit/
        assert res.status_int == 302
        assert res.headers['Location'].endswith("/u/chris/edit/")

        res = test_app.post(
            '/u/chris/edit/', {
                'bio': u'I love toast!',
                'url': u'http://dustycloud.org/'})

        test_user = User.query.filter_by(username=u'chris').first()
        assert test_user.bio == u'I love toast!'
        assert test_user.url == u'http://dustycloud.org/'

        # change a different user than the logged in (should fail with 403)
        fixture_add_user(username=u"foo")
        res = test_app.post(
            '/u/foo/edit/', {
                'bio': u'I love toast!',
                'url': u'http://dustycloud.org/'}, expect_errors=True)
        assert res.status_int == 403

        # test changing the bio and the URL inproperly
        too_long_bio = 150 * 'T' + 150 * 'o' + 150 * 'a' + 150 * 's' + 150* 't'

        test_app.post(
            '/u/chris/edit/', {
                # more than 500 characters
                'bio': too_long_bio,
                'url': 'this-is-no-url'})

        # Check form errors
        context = template.TEMPLATE_TEST_CONTEXT[
            'mediagoblin/edit/edit_profile.html']
        form = context['form']

        assert form.bio.errors == [
            u'Field must be between 0 and 500 characters long.']
        assert form.url.errors == [
            u'This address contains errors']

    def test_email_change(self, test_app):
        self.login(test_app)

        # Test email already in db
        template.clear_test_template_context()
        test_app.post(
            '/edit/account/', {
                'new_email': 'chris@example.com',
                'password': 'toast'})

        # Check form errors
        context = template.TEMPLATE_TEST_CONTEXT[
            'mediagoblin/edit/edit_account.html']
        assert context['form'].new_email.errors == [
            u'Sorry, a user with that email address already exists.']

        # Test successful email change
        template.clear_test_template_context()
        res = test_app.post(
            '/edit/account/', {
                'new_email': 'new@example.com',
                'password': 'toast'})
        res.follow()

        # Correct redirect?
        assert urlparse.urlsplit(res.location)[2] == '/u/chris/'

        # Make sure we get email verification and try verifying
        assert len(mail.EMAIL_TEST_INBOX) == 1
        message = mail.EMAIL_TEST_INBOX.pop()
        assert message['To'] == 'new@example.com'
        email_context = template.TEMPLATE_TEST_CONTEXT[
            'mediagoblin/edit/verification.txt']
        assert email_context['verification_url'] in \
            message.get_payload(decode=True)

        path = urlparse.urlsplit(email_context['verification_url'])[2]
        assert path == u'/edit/verify_email/'

        ## Try verifying with bs verification key, shouldn't work
        template.clear_test_template_context()
        res = test_app.get(
            "/edit/verify_email/?token=total_bs")
        res.follow()

        # Correct redirect?
        assert urlparse.urlsplit(res.location)[2] == '/'

        # Email shouldn't be saved
        email_in_db = mg_globals.database.User.query.filter_by(
            email='new@example.com').first()
        email = User.query.filter_by(username='chris').first().email
        assert email_in_db is None
        assert email == 'chris@example.com'

        # Verify email activation works
        template.clear_test_template_context()
        get_params = urlparse.urlsplit(email_context['verification_url'])[3]
        res = test_app.get('%s?%s' % (path, get_params))
        res.follow()

        # New email saved?
        email = User.query.filter_by(username='chris').first().email
        assert email == 'new@example.com'
# test changing the url inproperly
