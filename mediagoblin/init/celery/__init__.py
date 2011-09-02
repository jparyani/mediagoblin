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

import os
import sys


MANDATORY_CELERY_IMPORTS = ['mediagoblin.process_media']

DEFAULT_SETTINGS_MODULE = 'mediagoblin.init.celery.dummy_settings_module'


def setup_celery_from_config(app_config, global_config,
                             settings_module=DEFAULT_SETTINGS_MODULE,
                             force_celery_always_eager=False,
                             set_environ=True):
    """
    Take a mediagoblin app config and try to set up a celery settings
    module from this.

    Args:
    - app_config: the application config section
    - global_config: the entire ConfigObj loaded config, all sections
    - settings_module: the module to populate, as a string
    - force_celery_always_eager: whether or not to force celery into
      always eager mode; good for development and small installs
    - set_environ: if set, this will CELERY_CONFIG_MODULE to the
      settings_module
    """
    if global_config.has_key('celery'):
        celery_conf = global_config['celery']
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
        celery_mongo_settings['port'] = app_config['db_port']
        if celery_settings['BROKER_BACKEND'] == 'mongodb':
            celery_settings['BROKER_PORT'] = app_config['db_port']
    celery_mongo_settings['database'] = app_config['db_name']

    celery_settings['CELERY_MONGODB_BACKEND_SETTINGS'] = celery_mongo_settings

    # Add anything else
    for key, value in celery_conf.iteritems():
        key = key.upper()
        celery_settings[key] = value

    # add mandatory celery imports
    celery_imports = celery_settings.setdefault('CELERY_IMPORTS', [])
    celery_imports.extend(MANDATORY_CELERY_IMPORTS)

    if force_celery_always_eager:
        celery_settings['CELERY_ALWAYS_EAGER'] = True
        celery_settings['CELERY_EAGER_PROPAGATES_EXCEPTIONS'] = True

    __import__(settings_module)
    this_module = sys.modules[settings_module]

    for key, value in celery_settings.iteritems():
        setattr(this_module, key, value)
    
    if set_environ:
        os.environ['CELERY_CONFIG_MODULE'] = settings_module
