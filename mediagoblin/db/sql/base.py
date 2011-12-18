from sqlalchemy.orm import scoped_session, sessionmaker


Session = scoped_session(sessionmaker())


class GMGTableBase(object):
    query = Session.query_property()

    @classmethod
    def find(cls, query_dict={}):
        return cls.query.filter_by(**query_dict)

    @classmethod
    def find_one(cls, query_dict={}):
        return cls.query.filter_by(**query_dict).first()
