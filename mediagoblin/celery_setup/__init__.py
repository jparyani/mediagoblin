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
import sys

from paste.deploy.converters import asbool, asint, aslist


KNOWN_CONFIG_BOOLS = [
    'CELERY_RESULT_PERSISTENT',
    'CELERY_CREATE_MISSING_QUEUES',
    'BROKER_USE_SSL', 'BROKER_CONNECTION_RETRY',
    'CELERY_ALWAYS_EAGER', 'CELERY_EAGER_PROPAGATES_EXCEPTIONS',
    'CELERY_IGNORE_RESULT', 'CELERY_TRACK_STARTED',
    'CELERY_DISABLE_RATE_LIMITS', 'CELERY_ACKS_LATE',
    'CELERY_STORE_ERRORS_EVEN_IF_IGNORED',
    'CELERY_SEND_TASK_ERROR_EMAILS',
    'CELERY_SEND_EVENTS', 'CELERY_SEND_TASK_SENT_EVENT',
    'CELERYD_LOG_COLOR', 'CELERY_REDIRECT_STDOUTS',
    ]

KNOWN_CONFIG_INTS = [
    'CELERYD_CONCURRENCY',
    'CELERYD_PREFETCH_MULTIPLIER',
    'CELERY_AMQP_TASK_RESULT_EXPIRES',
    'CELERY_AMQP_TASK_RESULT_CONNECTION_MAX',
    'REDIS_PORT', 'REDIS_DB',
    'BROKER_PORT', 'BROKER_CONNECTION_TIMEOUT',
    'CELERY_BROKER_CONNECTION_MAX_RETRIES',
    'CELERY_TASK_RESULT_EXPIRES', 'CELERY_MAX_CACHED_RESULTS',
    'CELERY_DEFAULT_RATE_LIMIT', # ??
    'CELERYD_MAX_TASKS_PER_CHILD', 'CELERYD_TASK_TIME_LIMIT',
    'CELERYD_TASK_SOFT_TIME_LIMIT',
    'MAIL_PORT', 'CELERYBEAT_MAX_LOOP_INTERVAL',
    ]

KNOWN_CONFIG_FLOATS = [
    'CELERYD_ETA_SCHEDULER_PRECISION',
    ]

KNOWN_CONFIG_LISTS = [
    'CELERY_ROUTES', 'CELERY_IMPORTS',
    ]


## Needs special processing:
# ADMINS, ???
# there are a lot more; we should list here or process specially.


def asfloat(obj):
    try:
        return float(obj)
    except (TypeError, ValueError), e:
        raise ValueError(
            "Bad float value: %r" % obj)


MANDATORY_CELERY_IMPORTS = ['mediagoblin.process_media']

DEFAULT_SETTINGS_MODULE = 'mediagoblin.celery_setup.dummy_settings_module'

def setup_celery_from_config(app_config, global_config,
                             settings_module=DEFAULT_SETTINGS_MODULE,
                             force_celery_always_eager=False,
                             set_environ=True):
    """
    Take a mediagoblin app config and the global config from a paste
    factory and try to set up a celery settings module from this.

    Args:
    - app_config: the application config section
    - global_config: the entire paste config, all sections
    - settings_module: the module to populate, as a string
    - 
    - set_environ: if set, this will CELERY_CONFIG_MODULE to the
      settings_module
    """
    if asbool(app_config.get('use_celery_environment_var')) == True:
        # Don't setup celery based on our config file.
        return

    celery_conf_section = app_config.get('celery_section', 'celery')
    if global_config.has_key(celery_conf_section):
        celery_conf = global_config[celery_conf_section]
    else:
        celery_conf = {}
    
    celery_settings = {}

    # set up mongodb stuff
    celery_settings['CELERY_RESULT_BACKEND'] = 'mongodb'
    if not celery_settings.has_key('BROKER_BACKEND'):
        celery_settings['BROKER_BACKEND'] = 'mongodb'

    celery_mongo_settings = {}

    if app_config.has_key('db_host'):
        celery_mongo_settings['host'] = app_config['db_host']
        if celery_settings['BROKER_BACKEND'] == 'mongodb':
            celery_settings['BROKER_HOST'] = app_config['db_host']
    if app_config.has_key('db_port'):
        celery_mongo_settings['port'] = asint(app_config['db_port'])
        if celery_settings['BROKER_BACKEND'] == 'mongodb':
            celery_settings['BROKER_PORT'] = asint(app_config['db_port'])
    celery_mongo_settings['database'] = app_config.get('db_name', 'mediagoblin')

    celery_settings['CELERY_MONGODB_BACKEND_SETTINGS'] = celery_mongo_settings

    # Add anything else
    for key, value in celery_conf.iteritems():
        key = key.upper()
        if key in KNOWN_CONFIG_BOOLS:
            value = asbool(value)
        elif key in KNOWN_CONFIG_INTS:
            value = asint(value)
        elif key in KNOWN_CONFIG_FLOATS:
            value = asfloat(value)
        elif key in KNOWN_CONFIG_LISTS:
            value = aslist(value)
        celery_settings[key] = value

    # add mandatory celery imports
    celery_imports = celery_settings.setdefault('CELERY_IMPORTS', [])
    celery_imports.extend(MANDATORY_CELERY_IMPORTS)

    if force_celery_always_eager:
        celery_settings['CELERY_ALWAYS_EAGER'] = True

    __import__(settings_module)
    this_module = sys.modules[settings_module]

    for key, value in celery_settings.iteritems():
        setattr(this_module, key, value)
    
    if set_environ:
        os.environ['CELERY_CONFIG_MODULE'] = settings_module
