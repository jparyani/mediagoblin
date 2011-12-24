from sqlalchemy.orm import scoped_session, sessionmaker


Session = scoped_session(sessionmaker())


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
        retval = cls.find_one(query_dict)
        assert retval is not None
        return retval
