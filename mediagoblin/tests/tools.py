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


import os
import pkg_resources
import shutil

from functools import wraps

from paste.deploy import loadapp
from webtest import TestApp

from mediagoblin import mg_globals
from mediagoblin.db.models import User, MediaEntry, Collection
from mediagoblin.tools import testing
from mediagoblin.init.config import read_mediagoblin_config
from mediagoblin.db.open import setup_connection_and_db_from_config
from mediagoblin.db.base import Session
from mediagoblin.meddleware import BaseMeddleware
from mediagoblin.auth.lib import bcrypt_gen_password_hash
from mediagoblin.gmg_commands.dbupdate import run_dbupdate
from mediagoblin.init.celery import setup_celery_app


MEDIAGOBLIN_TEST_DB_NAME = u'__mediagoblin_tests__'
TEST_SERVER_CONFIG = pkg_resources.resource_filename(
    'mediagoblin.tests', 'test_paste.ini')
TEST_APP_CONFIG = pkg_resources.resource_filename(
    'mediagoblin.tests', 'test_mgoblin_app.ini')
TEST_USER_DEV = pkg_resources.resource_filename(
    'mediagoblin.tests', 'test_user_dev')
MGOBLIN_APP = None

USER_DEV_DIRECTORIES_TO_SETUP = [
    'media/public', 'media/queue',
    'beaker/sessions/data', 'beaker/sessions/lock']

BAD_CELERY_MESSAGE = """\
Sorry, you *absolutely* must run nosetests with the
mediagoblin.init.celery.from_tests module.  Like so:
$ CELERY_CONFIG_MODULE=mediagoblin.init.celery.from_tests ./bin/nosetests"""


class BadCeleryEnviron(Exception): pass


class TestingMeddleware(BaseMeddleware):
    """
    Meddleware for the Unit tests

    It might make sense to perform some tests on all
    requests/responses. Or prepare them in a special
    manner. For example all html responses could be tested
    for being valid html *after* being rendered.

    This module is getting inserted at the front of the
    meddleware list, which means: requests are handed here
    first, responses last. So this wraps up the "normal"
    app.

    If you need to add a test, either add it directly to
    the appropiate process_request or process_response, or
    create a new method and call it from process_*.
    """

    def process_response(self, request, response):
        # All following tests should be for html only!
        if getattr(response, 'content_type', None) != "text/html":
            # Get out early
            return

        # If the template contains a reference to
        # /mgoblin_static/ instead of using
        # /request.staticdirect(), error out here.
        # This could probably be implemented as a grep on
        # the shipped templates easier...
        if response.text.find("/mgoblin_static/") >= 0:
            raise AssertionError(
                "Response HTML contains reference to /mgoblin_static/ "
                "instead of staticdirect. Request was for: "
                + request.full_path)

        return


def suicide_if_bad_celery_environ():
    if not os.environ.get('CELERY_CONFIG_MODULE') == \
            'mediagoblin.init.celery.from_tests':
        raise BadCeleryEnviron(BAD_CELERY_MESSAGE)


def get_app(dump_old_app=True):
    suicide_if_bad_celery_environ()

    # Make sure we've turned on testing
    testing._activate_testing()

    # Leave this imported as it sets up celery.
    from mediagoblin.init.celery import from_tests

    global MGOBLIN_APP

    # Just return the old app if that exists and it's okay to set up
    # and return
    if MGOBLIN_APP and not dump_old_app:
        return MGOBLIN_APP

    Session.rollback()
    Session.remove()

    # Remove and reinstall user_dev directories
    if os.path.exists(TEST_USER_DEV):
        shutil.rmtree(TEST_USER_DEV)

    for directory in USER_DEV_DIRECTORIES_TO_SETUP:
        full_dir = os.path.join(TEST_USER_DEV, directory)
        os.makedirs(full_dir)

    # Get app config
    global_config, validation_result = read_mediagoblin_config(TEST_APP_CONFIG)
    app_config = global_config['mediagoblin']

    # Run database setup/migrations
    run_dbupdate(app_config, global_config)

    # setup app and return
    test_app = loadapp(
        'config:' + TEST_SERVER_CONFIG)

    # Re-setup celery
    setup_celery_app(app_config, global_config)

    # Insert the TestingMeddleware, which can do some
    # sanity checks on every request/response.
    # Doing it this way is probably not the cleanest way.
    # We'll fix it, when we have plugins!
    mg_globals.app.meddleware.insert(0, TestingMeddleware(mg_globals.app))

    app = TestApp(test_app)
    MGOBLIN_APP = app

    return app


def setup_fresh_app(func):
    """
    Decorator to setup a fresh test application for this function.

    Cleans out test buckets and passes in a new, fresh test_app.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        test_app = get_app()
        testing.clear_test_buckets()
        return func(test_app, *args, **kwargs)

    return wrapper


def install_fixtures_simple(db, fixtures):
    """
    Very simply install fixtures in the database
    """
    for collection_name, collection_fixtures in fixtures.iteritems():
        collection = db[collection_name]
        for fixture in collection_fixtures:
            collection.insert(fixture)


def assert_db_meets_expected(db, expected):
    """
    Assert a database contains the things we expect it to.

    Objects are found via 'id', so you should make sure your document
    has an id.

    Args:
     - db: pymongo or mongokit database connection
     - expected: the data we expect.  Formatted like:
         {'collection_name': [
             {'id': 'foo',
              'some_field': 'some_value'},]}
    """
    for collection_name, collection_data in expected.iteritems():
        collection = db[collection_name]
        for expected_document in collection_data:
            document = collection.find_one({'id': expected_document['id']})
            assert document is not None  # make sure it exists
            assert document == expected_document  # make sure it matches


def fixture_add_user(username=u'chris', password=u'toast',
                     active_user=True):
    # Reuse existing user or create a new one
    test_user = User.query.filter_by(username=username).first()
    if test_user is None:
        test_user = User()
    test_user.username = username
    test_user.email = username + u'@example.com'
    if password is not None:
        test_user.pw_hash = bcrypt_gen_password_hash(password)
    if active_user:
        test_user.email_verified = True
        test_user.status = u'active'

    test_user.save()

    # Reload
    test_user = User.query.filter_by(username=username).first()

    # ... and detach from session:
    Session.expunge(test_user)

    return test_user


def fixture_media_entry(title=u"Some title", slug=None,
                        uploader=None, save=True, gen_slug=True):
    entry = MediaEntry()
    entry.title = title
    entry.slug = slug
    entry.uploader = uploader or fixture_add_user().id
    entry.media_type = u'image'
    
    if gen_slug:
        entry.generate_slug()
    if save:
        entry.save()

    return entry


def fixture_add_collection(name=u"My first Collection", user=None):
    if user is None:
        user = fixture_add_user()
    coll = Collection.query.filter_by(creator=user.id, title=name).first()
    if coll is not None:
        return coll
    coll = Collection()
    coll.creator = user.id
    coll.title = name
    coll.generate_slug()
    coll.save()

    # Reload
    Session.refresh(coll)

    # ... and detach from session:
    Session.expunge(coll)

    return coll
