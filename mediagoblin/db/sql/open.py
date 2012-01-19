# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011,2012 MediaGoblin contributors.  See AUTHORS.
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


from sqlalchemy import create_engine

from mediagoblin.db.sql.base import Session
from mediagoblin.db.sql.models import Base


class DatabaseMaster(object):
    def __init__(self, engine):
        self.engine = engine

        for k, v in Base._decl_class_registry.iteritems():
            setattr(self, k, v)

    def commit(self):
        Session.commit()

    def save(self, obj):
        Session.add(obj)
        Session.flush()

    def reset_after_request(self):
        Session.remove()


def setup_connection_and_db_from_config(app_config):
    engine = create_engine(app_config['sql_engine'], echo=True)
    Session.configure(bind=engine)

    return "dummy conn", DatabaseMaster(engine)


def check_db_migrations_current(db):
    pass
