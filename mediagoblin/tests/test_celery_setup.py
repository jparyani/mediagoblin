# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 MediaGoblin contributors.  See AUTHORS.
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

from mediagoblin.init import celery as celery_setup
from mediagoblin.init.config import read_mediagoblin_config


TEST_CELERY_CONF_NOSPECIALDB = pkg_resources.resource_filename(
    'mediagoblin.tests', 'fake_celery_conf.ini')
TEST_CELERY_CONF_MGSPECIALDB = pkg_resources.resource_filename(
    'mediagoblin.tests', 'fake_celery_conf_mgdb.ini')


def test_setup_celery_from_config():
    def _wipe_testmodule_clean(module):
        vars_to_wipe = [
            var for var in dir(module)
            if not var.startswith('__') and not var.endswith('__')]
        for var in vars_to_wipe:
            delattr(module, var)

    global_config, validation_result = read_mediagoblin_config(
        TEST_CELERY_CONF_NOSPECIALDB)
    app_config = global_config['mediagoblin']

    celery_setup.setup_celery_from_config(
        app_config, global_config,
        'mediagoblin.tests.fake_celery_module', set_environ=False)

    from mediagoblin.tests import fake_celery_module
    assert fake_celery_module.SOME_VARIABLE == 'floop'
    assert fake_celery_module.MAIL_PORT == 2000
    assert isinstance(fake_celery_module.MAIL_PORT, int)
    assert fake_celery_module.CELERYD_ETA_SCHEDULER_PRECISION == 1.3
    assert isinstance(fake_celery_module.CELERYD_ETA_SCHEDULER_PRECISION, float)
    assert fake_celery_module.CELERY_RESULT_PERSISTENT is True
    assert fake_celery_module.CELERY_IMPORTS == [
        'foo.bar.baz', 'this.is.an.import', 'mediagoblin.process_media']
    assert fake_celery_module.CELERY_MONGODB_BACKEND_SETTINGS == {
        'database': 'mediagoblin'}
    assert fake_celery_module.CELERY_RESULT_BACKEND == 'mongodb'
    assert fake_celery_module.BROKER_BACKEND == 'mongodb'

    _wipe_testmodule_clean(fake_celery_module)

    global_config, validation_result = read_mediagoblin_config(
        TEST_CELERY_CONF_MGSPECIALDB)
    app_config = global_config['mediagoblin']

    celery_setup.setup_celery_from_config(
        app_config, global_config,
        'mediagoblin.tests.fake_celery_module', set_environ=False)
    
    from mediagoblin.tests import fake_celery_module
    assert fake_celery_module.SOME_VARIABLE == 'poolf'
    assert fake_celery_module.MAIL_PORT == 2020
    assert isinstance(fake_celery_module.MAIL_PORT, int)
    assert fake_celery_module.CELERYD_ETA_SCHEDULER_PRECISION == 3.1
    assert isinstance(fake_celery_module.CELERYD_ETA_SCHEDULER_PRECISION, float)
    assert fake_celery_module.CELERY_RESULT_PERSISTENT is False
    assert fake_celery_module.CELERY_IMPORTS == [
        'baz.bar.foo', 'import.is.a.this', 'mediagoblin.process_media']
    assert fake_celery_module.CELERY_MONGODB_BACKEND_SETTINGS == {
        'database': 'captain_lollerskates',
        'host': 'mongodb.example.org',
        'port': 8080}
    assert fake_celery_module.CELERY_RESULT_BACKEND == 'mongodb'
    assert fake_celery_module.BROKER_BACKEND == 'mongodb'
    assert fake_celery_module.BROKER_HOST == 'mongodb.example.org'
    assert fake_celery_module.BROKER_PORT == 8080
