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
import logging

from mediagoblin.tools import pluginapi
from raven import Client
from raven.contrib.celery import register_signal

_log = logging.getLogger(__name__)

PLUGIN_DIR = os.path.dirname(__file__)


def setup_plugin():
    config = pluginapi.get_config('mediagoblin.plugins.oauth')

    _log.info('Setting up raven for celery...')

    sentry_dsn = config.get('sentry_dsn')

    if sentry_dsn:
        _log.info('Setting up raven from plugin config: {0}'.format(
            sentry_dsn))
        client = Client(sentry_dsn))
    elif os.environ.get('SENTRY_DSN'):
        _log.info('Setting up raven from SENTRY_DSN environment variable: {0}'\
                  .format(os.environ.get('SENTRY_DSN')))
        client = Client()  # Implicitly looks for SENTRY_DSN

    if client:
        register_signal(client)
    else:
        _log.error('Could not set up client, missing sentry DSN')

hooks = {
    'setup': setup_plugin,
    }
