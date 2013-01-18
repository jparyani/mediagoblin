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

from mediagoblin.tests.tools import get_app
from mediagoblin import mg_globals


def test_csrf_cookie_set():
    test_app = get_app(dump_old_app=False)
    cookie_name = mg_globals.app_config['csrf_cookie_name']

    # get login page
    response = test_app.get('/auth/login/')

    # assert that the mediagoblin nonce cookie has been set
    assert 'Set-Cookie' in response.headers
    assert cookie_name in response.cookies_set

    # assert that we're also sending a vary header
    assert response.headers.get('Vary', False) == 'Cookie'


def test_csrf_token_must_match():
    # We need a fresh app for this test on webtest < 1.3.6.
    # We do not understand why, but it fixes the tests.
    # If we require webtest >= 1.3.6, we can switch to a non fresh app here.
    test_app = get_app(dump_old_app=True)

    # construct a request with no cookie or form token
    assert test_app.post('/auth/login/',
                         extra_environ={'gmg.verify_csrf': True},
                         expect_errors=True).status_int == 403

    # construct a request with a cookie, but no form token
    assert test_app.post('/auth/login/',
                         headers={'Cookie': str('%s=foo' %
                                  mg_globals.app_config['csrf_cookie_name'])},
                         extra_environ={'gmg.verify_csrf': True},
                         expect_errors=True).status_int == 403

    # if both the cookie and form token are provided, they must match
    assert test_app.post('/auth/login/',
                         {'csrf_token': 'blarf'},
                         headers={'Cookie': str('%s=foo' %
                                  mg_globals.app_config['csrf_cookie_name'])},
                         extra_environ={'gmg.verify_csrf': True},
                         expect_errors=True).\
                         status_int == 403

    assert test_app.post('/auth/login/',
                         {'csrf_token': 'foo'},
                         headers={'Cookie': str('%s=foo' %
                                  mg_globals.app_config['csrf_cookie_name'])},
                         extra_environ={'gmg.verify_csrf': True}).\
                         status_int == 200

def test_csrf_exempt():
    test_app = get_app(dump_old_app=False)
    # monkey with the views to decorate a known endpoint
    import mediagoblin.auth.views
    from mediagoblin.meddleware.csrf import csrf_exempt

    mediagoblin.auth.views.login = csrf_exempt(
        mediagoblin.auth.views.login
    )

    # construct a request with no cookie or form token
    assert test_app.post('/auth/login/',
                         extra_environ={'gmg.verify_csrf': True},
                         expect_errors=False).status_int == 200

    # restore the CSRF protection in case other tests expect it
    mediagoblin.auth.views.login.csrf_enabled = True
