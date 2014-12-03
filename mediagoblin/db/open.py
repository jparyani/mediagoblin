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


from contextlib import contextmanager
import logging

import six
from sqlalchemy import create_engine, event

from mediagoblin import mg_globals
from mediagoblin.db.base import Base

_log = logging.getLogger(__name__)

from mediagoblin.tools.transition import DISABLE_GLOBALS

def set_models_as_attributes(obj):
    """
    Set all models as attributes on this object, for convenience

    TODO: This should eventually be deprecated.
    """
    for k, v in six.iteritems(Base._decl_class_registry):
        setattr(obj, k, v)


if not DISABLE_GLOBALS:
    from mediagoblin.db.base import Session

    class DatabaseMaster(object):
        def __init__(self, engine):
            self.engine = engine

            set_models_as_attributes(self)

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

        @property
        def query(self):
            return Session.query

else:
    from sqlalchemy.orm import sessionmaker

    class DatabaseManager(object):
        """
        Manage database connections.

        The main method here is session_scope which can be used with a
        "with" statement to get a session that is properly torn down
        by the end of execution.
        """
        def __init__(self, engine):
            self.engine = engine
            self.Session = sessionmaker(bind=engine)
            set_models_as_attributes(self)

        @contextmanager
        def session_scope(self):
            """
            This is a context manager, use like::

              with dbmanager.session_scope() as request.db:
                  some_view(request)
            """
            session = self.Session()

            #####################################
            # Functions to emulate DatabaseMaster
            #####################################
            def save(obj):
                session.add(obj)
                session.flush()

            def check_session_clean():
                # Is this implemented right?
                for dummy in session:
                    _log.warn("STRANGE: There are elements in the sql session. "
                              "Please report this and help us track this down.")
                    break

            def reset_after_request():
                session.rollback()
                session.remove()

            # now attach
            session.save = save
            session.check_session_clean = check_session_clean
            session.reset_after_request = reset_after_request

            set_models_as_attributes(session)
            #####################################

            try:
                yield session
            finally:
                session.rollback()
                session.close()



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


def setup_connection_and_db_from_config(app_config, migrations=False, app=None):
    engine = create_engine(app_config['sql_engine'])

    # @@: Maybe make a weak-ref so an engine can get garbage
    # collected?  Not that we expect to make a lot of MediaGoblinApp
    # instances in a single process...
    engine.app = app

    # Enable foreign key checking for sqlite
    if app_config['sql_engine'].startswith('sqlite://'):
        if migrations:
            event.listen(engine, 'connect',
                         _sqlite_disable_fk_pragma_on_connect)
        else:
            event.listen(engine, 'connect', _sqlite_fk_pragma_on_connect)

    # logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    if DISABLE_GLOBALS:
        return DatabaseManager(engine)

    else:
        Session.configure(bind=engine)

        return DatabaseMaster(engine)


def check_db_migrations_current(db):
    pass
