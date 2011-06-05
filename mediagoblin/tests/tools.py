# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 Free Software Foundation, Inc
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


import pkg_resources
import os, shutil

from paste.deploy import appconfig, loadapp
from webtest import TestApp

from mediagoblin.db.open import setup_connection_and_db_from_config


MEDIAGOBLIN_TEST_DB_NAME = '__mediagoblinunittests__'
TEST_APP_CONFIG = pkg_resources.resource_filename(
    'mediagoblin.tests', 'mgoblin_test_app.ini')
TEST_USER_DEV = pkg_resources.resource_filename(
    'mediagoblin.tests', 'test_user_dev')
MGOBLIN_APP = None

USER_DEV_DIRECTORIES_TO_SETUP = [
    'media/public', 'media/queue',
    'beaker/sessions/data', 'beaker/sessions/lock']


class BadCeleryEnviron(Exception): pass


def get_test_app(dump_old_app=True):
    if not os.environ.get('CELERY_CONFIG_MODULE') == \
            'mediagoblin.celery_setup.from_tests':
        raise BadCeleryEnviron(
            u"Sorry, you *absolutely* must run nosetests with the\n"
            u"mediagoblin.celery_setup.from_tests module.  Like so:\n"
            u"$ CELERY_CONFIG_MODULE=mediagoblin.celery_setup.from_tests ./bin/nosetests")

    # Just return the old app if that exists and it's okay to set up
    # and return
    if MGOBLIN_APP and not dump_old_app:
        return MGOBLIN_APP

    # Remove and reinstall user_dev directories
    if os.path.exists(TEST_USER_DEV):
        shutil.rmtree(TEST_USER_DEV)

    for directory in USER_DEV_DIRECTORIES_TO_SETUP:
        full_dir = os.path.join(TEST_USER_DEV, directory)
        os.makedirs(full_dir)

    # Get app config
    config = appconfig(
        'config:' + os.path.basename(TEST_APP_CONFIG),
        relative_to=os.path.dirname(TEST_APP_CONFIG),
        name='mediagoblin')

    # Wipe database
    # @@: For now we're dropping collections, but we could also just
    # collection.remove() ?
    connection, db = setup_connection_and_db_from_config(
        config.local_conf)

    collections_to_wipe = [
        collection
        for collection in db.collection_names()
        if not collection.startswith('system.')]

    for collection in collections_to_wipe:
        db.drop_collection(collection)

    # Don't need these anymore...
    del(connection)
    del(db)

    # TODO: Drop and recreate indexes

    # setup app and return
    test_app = loadapp(
        'config:' + TEST_APP_CONFIG)

    return TestApp(test_app)
