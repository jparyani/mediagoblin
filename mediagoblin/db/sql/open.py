from sqlalchemy import create_engine

from mediagoblin.db.sql.base import Session
from mediagoblin.db.sql.models import Base


class DatabaseMaster(object):
    def __init__(self, engine):
        self.engine = engine

        for k,v in Base._decl_class_registry.iteritems():
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
