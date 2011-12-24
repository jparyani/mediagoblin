from sqlalchemy.orm import scoped_session, sessionmaker, object_session
from sqlalchemy.orm.query import Query
from sqlalchemy.sql.expression import desc
from mediagoblin.db.sql.fake import DESCENDING


def _get_query_model(query):
    cols = query.column_descriptions
    assert len(cols) == 1, "These functions work only on simple queries"
    return cols[0]["type"]


class GMGQuery(Query):
    def sort(self, key, direction):
        key_col = getattr(_get_query_model(self), key)
        if direction is DESCENDING:
            key_col = desc(key_col)
        return self.order_by(key_col)

    def skip(self, amount):
        return self.offset(amount)


Session = scoped_session(sessionmaker(query_cls=GMGQuery))


def _fix_query_dict(query_dict):
    if '_id' in query_dict:
        query_dict['id'] = query_dict.pop('_id')


class GMGTableBase(object):
    query = Session.query_property()

    @classmethod
    def find(cls, query_dict={}):
        _fix_query_dict(query_dict)
        return cls.query.filter_by(**query_dict)

    @classmethod
    def find_one(cls, query_dict={}):
        _fix_query_dict(query_dict)
        return cls.query.filter_by(**query_dict).first()

    @classmethod
    def one(cls, query_dict):
        return cls.find(query_dict).one()

    def get(self, key):
        return getattr(self, key)

    def save(self, validate = True):
        assert validate
        sess = object_session(self)
        if sess is None:
            sess = Session()
        sess.add(self)
        sess.commit()
