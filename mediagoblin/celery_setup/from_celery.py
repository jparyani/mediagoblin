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

from paste.deploy.loadwsgi import NicerConfigParser
from paste.deploy.converters import asbool

from mediagoblin import storage
from mediagoblin.db.open import setup_connection_and_db_from_config
from mediagoblin.celery_setup import setup_celery_from_config
from mediagoblin.globals import setup_globals
from mediagoblin import globals as mgoblin_globals


OUR_MODULENAME = 'mediagoblin.celery_setup.from_celery'


def setup_self(setup_globals_func=setup_globals):
    """
    Transform this module into a celery config module by reading the
    mediagoblin config file.  Set the environment variable
    MEDIAGOBLIN_CONFIG to specify where this config file is at and
    what section it uses.

    By default it defaults to 'mediagoblin.ini:app:mediagoblin'.

    The first colon ":" is a delimiter between the filename and the
    config section, so in this case the filename is 'mediagoblin.ini'
    and the section where mediagoblin is defined is 'app:mediagoblin'.

    Args:
    - 'setup_globals_func': this is for testing purposes only.  Don't
      set this!
    """
    mgoblin_conf_file, mgoblin_section = os.environ.get(
        'MEDIAGOBLIN_CONFIG', 'mediagoblin.ini:app:mediagoblin').split(':', 1)
    if not os.path.exists(mgoblin_conf_file):
        raise IOError(
            "MEDIAGOBLIN_CONFIG not set or file does not exist")
        
    parser = NicerConfigParser(mgoblin_conf_file)
    parser.read(mgoblin_conf_file)
    parser._defaults.setdefault(
        'here', os.path.dirname(os.path.abspath(mgoblin_conf_file)))
    parser._defaults.setdefault(
        '__file__', os.path.abspath(mgoblin_conf_file))

    mgoblin_section = dict(parser.items(mgoblin_section))
    mgoblin_conf = dict(
        [(section_name, dict(parser.items(section_name)))
         for section_name in parser.sections()])
    setup_celery_from_config(
        mgoblin_section, mgoblin_conf,
        settings_module=OUR_MODULENAME,
        set_environ=False)

    connection, db = setup_connection_and_db_from_config(mgoblin_section)

    # Set up the storage systems.
    public_store = storage.storage_system_from_paste_config(
        mgoblin_section, 'publicstore')
    queue_store = storage.storage_system_from_paste_config(
        mgoblin_section, 'queuestore')

    setup_globals_func(
        db_connection=connection,
        database=db,
        public_store=public_store,
        email_debug_mode=asbool(mgoblin_section.get('email_debug_mode')),
        email_sender_address=mgoblin_section.get(
            'email_sender_address', 
            'notice@mediagoblin.example.org'),
        queue_store=queue_store)


if os.environ['CELERY_CONFIG_MODULE'] == OUR_MODULENAME:
    setup_self()
