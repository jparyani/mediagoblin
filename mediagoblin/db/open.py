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


from sqlalchemy import create_engine, event
import logging

import six

from mediagoblin.db.base import Base, Session
from mediagoblin import mg_globals

_log = logging.getLogger(__name__)


class DatabaseMaster(object):
    def __init__(self, engine):
        self.engine = engine

        for k, v in six.iteritems(Base._decl_class_registry):
            setattr(self, k, v)

    def commit(self):
        Session.commit()

    def save(self, obj):
        Session.add(obj)
        Session.flush()

    def check_session_clean(self):
        for dummy in Session():
            _log.warn("STRANGE: There are elements in the sql session. "
                      "Please report this and help us track this down.")
            break

    def reset_after_request(self):
        Session.rollback()
        Session.remove()


def load_models(app_config):
    import mediagoblin.db.models

    for plugin in mg_globals.global_config.get('plugins', {}).keys():
        _log.debug("Loading %s.models", plugin)
        try:
            __import__(plugin + ".models")
        except ImportError as exc:
            _log.debug("Could not load {0}.models: {1}".format(
                plugin,
                exc))


def _sqlite_fk_pragma_on_connect(dbapi_con, con_record):
    """Enable foreign key checking on each new sqlite connection"""
    dbapi_con.execute('pragma foreign_keys=on')


def _sqlite_disable_fk_pragma_on_connect(dbapi_con, con_record):
    """
    Disable foreign key checking on each new sqlite connection
    (Good for migrations!)
    """
    dbapi_con.execute('pragma foreign_keys=off')


def setup_connection_and_db_from_config(app_config, migrations=False):
    engine = create_engine(app_config['sql_engine'])

    # Enable foreign key checking for sqlite
    if app_config['sql_engine'].startswith('sqlite://'):
        if migrations:
            event.listen(engine, 'connect',
                         _sqlite_disable_fk_pragma_on_connect)
        else:
            event.listen(engine, 'connect', _sqlite_fk_pragma_on_connect)

    # logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    Session.configure(bind=engine)

    return DatabaseMaster(engine)


def check_db_migrations_current(db):
    pass
