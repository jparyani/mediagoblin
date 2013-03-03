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

_log = logging.getLogger(__name__)


def get_client():
    from raven import Client
    config = pluginapi.get_config('mediagoblin.plugins.raven')

    sentry_dsn = config.get('sentry_dsn')

    client = None

    if sentry_dsn:
        _log.info('Setting up raven from plugin config: {0}'.format(
            sentry_dsn))
        client = Client(sentry_dsn)
    elif os.environ.get('SENTRY_DSN'):
        _log.info('Setting up raven from SENTRY_DSN environment variable: {0}'\
                  .format(os.environ.get('SENTRY_DSN')))
        client = Client()  # Implicitly looks for SENTRY_DSN

    if not client:
        _log.error('Could not set up client, missing sentry DSN')
        return None

    return client


def setup_celery():
    from raven.contrib.celery import register_signal

    client = get_client()

    register_signal(client)


def setup_logging():
    config = pluginapi.get_config('mediagoblin.plugins.raven')

    conf_setup_logging = False
    if config.get('setup_logging'):
        conf_setup_logging = bool(int(config.get('setup_logging')))

    if not conf_setup_logging:
        return

    from raven.handlers.logging import SentryHandler
    from raven.conf import setup_logging

    client = get_client()

    _log.info('Setting up raven logging handler')

    setup_logging(SentryHandler(client))


def wrap_wsgi(app):
    from raven.middleware import Sentry

    client = get_client()

    _log.info('Attaching raven middleware...')

    return Sentry(app, client)


hooks = {
    'setup': setup_logging,
    'wrap_wsgi': wrap_wsgi,
    'celery_logging_setup': setup_logging,
    'celery_setup': setup_celery,
    }
