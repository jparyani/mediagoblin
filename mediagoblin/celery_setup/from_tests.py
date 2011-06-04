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

import os

from mediagoblin.tests.tools import TEST_APP_CONFIG
from mediagoblin import util
from mediagoblin.celery_setup import setup_celery_from_config
from mediagoblin.globals import setup_globals


OUR_MODULENAME = 'mediagoblin.celery_setup.from_tests'


def setup_self(setup_globals_func=setup_globals):
    """
    Set up celery for testing's sake, which just needs to set up
    celery and celery only.
    """
    mgoblin_conf = util.read_config_file(TEST_APP_CONFIG)
    mgoblin_section = mgoblin_conf['app:mediagoblin']

    setup_celery_from_config(
        mgoblin_section, mgoblin_conf,
        settings_module=OUR_MODULENAME,
        set_environ=False)


if os.environ.get('CELERY_CONFIG_MODULE') == OUR_MODULENAME:
    setup_self()
