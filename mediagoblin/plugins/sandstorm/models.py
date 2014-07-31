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


from datetime import datetime, timedelta


from sqlalchemy import Column, Unicode, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref
from mediagoblin.db.base import Base
from mediagoblin.db.models import User

# Don't remove this, I *think* it applies sqlalchemy-migrate functionality onto
# the models.
from migrate import changeset

class SandstormUser(Base):
    __tablename__ = 'sandstorm__user'

    id = Column(Integer, primary_key=True)
    sandstorm_user_id = Column(Unicode, unique=True, index=True)

    user_id = Column(Integer, ForeignKey(User.id))
    user = relationship(
        User,
        backref=backref('sandstorm_user_relation',
                        cascade='all, delete-orphan'))

    def __repr__(self):
        return '<{0} {1}:{2}>'.format(
                self.__class__.__name__,
                self.id,
                self.sandstorm_user_id.encode('ascii', 'replace'))



MODELS = [SandstormUser]
