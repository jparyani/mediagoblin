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

import jinja2

from mediagoblin.tools import staticdirect
from mediagoblin.tools.translate import set_available_locales
from mediagoblin.init.config import (
    read_mediagoblin_config, generate_validation_report)
from mediagoblin import mg_globals
from mediagoblin.mg_globals import setup_globals
from mediagoblin.db.open import setup_connection_and_db_from_config, \
    check_db_migrations_current, load_models
from mediagoblin.tools.workbench import WorkbenchManager
from mediagoblin.storage import storage_system_from_config


class Error(Exception):
    pass


class ImproperlyConfigured(Error):
    pass


def setup_locales():
    """Checks which language translations are available and sets them"""
    set_available_locales()


def setup_global_and_app_config(config_path):
    global_config, validation_result = read_mediagoblin_config(config_path)
    app_config = global_config['mediagoblin']
    # report errors if necessary
    validation_report = generate_validation_report(
        global_config, validation_result)
    if validation_report:
        raise ImproperlyConfigured(validation_report)

    setup_globals(
        app_config=app_config,
        global_config=global_config)

    return global_config, app_config


def setup_database():
    app_config = mg_globals.app_config

    # Load all models for media types (plugins, ...)
    load_models(app_config)

    # Set up the database
    db = setup_connection_and_db_from_config(app_config)

    check_db_migrations_current(db)

    setup_globals(database=db)

    return db


def get_jinja_loader(user_template_path=None, current_theme=None,
                     plugin_template_paths=None):
    """
    Set up the Jinja template loaders, possibly allowing for user
    overridden templates.

    (In the future we may have another system for providing theming;
    for now this is good enough.)
    """
    path_list = []

    # Add user path first--this takes precedence over everything.
    if user_template_path is not None:
        path_list.append(jinja2.FileSystemLoader(user_template_path))

    # Any theme directories in the registry
    if current_theme and current_theme.get('templates_dir'):
        path_list.append(
            jinja2.FileSystemLoader(
                current_theme['templates_dir']))

    # Add plugin template paths next--takes precedence over
    # core templates.
    if plugin_template_paths is not None:
        path_list.extend((jinja2.FileSystemLoader(path)
                          for path in plugin_template_paths))

    # Add core templates last.
    path_list.append(jinja2.PackageLoader('mediagoblin', 'templates'))

    return jinja2.ChoiceLoader(path_list)


def get_staticdirector(app_config):
    # At minimum, we need the direct_remote_path
    if not 'direct_remote_path' in app_config \
            or not 'theme_web_path' in app_config:
        raise ImproperlyConfigured(
            "direct_remote_path and theme_web_path must be provided")

    direct_domains = {None: app_config['direct_remote_path'].strip()}
    direct_domains['theme'] = app_config['theme_web_path'].strip()

    return staticdirect.StaticDirect(
        direct_domains)


def setup_storage():
    global_config = mg_globals.global_config

    key_short = 'publicstore'
    key_long = "storage:" + key_short
    public_store = storage_system_from_config(global_config[key_long])

    key_short = 'queuestore'
    key_long = "storage:" + key_short
    queue_store = storage_system_from_config(global_config[key_long])

    setup_globals(
        public_store=public_store,
        queue_store=queue_store)

    return public_store, queue_store


def setup_workbench():
    app_config = mg_globals.app_config

    workbench_manager = WorkbenchManager(app_config['workbench_path'])

    setup_globals(workbench_manager=workbench_manager)
