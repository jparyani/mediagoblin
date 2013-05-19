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


from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, object_session

Session = scoped_session(sessionmaker())


class GMGTableBase(object):
    query = Session.query_property()

    @classmethod
    def find(cls, query_dict):
        return cls.query.filter_by(**query_dict)

    @classmethod
    def find_one(cls, query_dict):
        return cls.query.filter_by(**query_dict).first()

    @classmethod
    def one(cls, query_dict):
        return cls.find(query_dict).one()

    def get(self, key):
        return getattr(self, key)

    def setdefault(self, key, defaultvalue):
        # The key *has* to exist on sql.
        return getattr(self, key)

    def save(self):
        sess = object_session(self)
        if sess is None:
            sess = Session()
        sess.add(self)
        sess.commit()

    def delete(self, commit=True):
        """Delete the object and commit the change immediately by default"""
        sess = object_session(self)
        assert sess is not None, "Not going to delete detached %r" % self
        sess.delete(self)
        if commit:
            sess.commit()


Base = declarative_base(cls=GMGTableBase)


class DictReadAttrProxy(object):
    """
    Maps read accesses to obj['key'] to obj.key
    and hides all the rest of the obj
    """
    def __init__(self, proxied_obj):
        self.proxied_obj = proxied_obj

    def __getitem__(self, key):
        try:
            return getattr(self.proxied_obj, key)
        except AttributeError:
            raise KeyError("%r is not an attribute on %r"
                % (key, self.proxied_obj))
