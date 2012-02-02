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

from mediagoblin.tests.tools import TEST_APP_CONFIG
from mediagoblin.init.celery.from_celery import setup_self


OUR_MODULENAME = __name__
CELERY_SETUP = False


if os.environ.get('CELERY_CONFIG_MODULE') == OUR_MODULENAME:
    if CELERY_SETUP:
        pass
    else:
        setup_self(check_environ_for_conf=False, module_name=OUR_MODULENAME,
                   default_conf_file=TEST_APP_CONFIG)
        CELERY_SETUP = True
