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
from sqlalchemy import Column, Integer, Unicode, ForeignKey
from sqlalchemy.orm import relationship, backref

from mediagoblin.db.base import Base
from mediagoblin.db.models import MediaEntry, Privilege

BACKREF_NAME = "archivalook__featured"


class FeaturedMedia(Base):
    """
    A table which logs which media are featured so that they can be displayed on
    the front page.

    :keyword    media_entry_id                  An integer foreign key which
                                                indicates which media entry this
                                                feature describes.
    :keyword    display_type                    A string to describe how
                                                prominently this feature will be
                                                displayed. The three appropriate
                                                values are 'primary',
                                                'secondary' and 'tertiary'
    :keyword    order                           An integer describing this
                                                feature's place in the "stack"
                                                which is displayed to the site's
                                                visitor. This value should begin
                                                at 0 (for the top) and increase
                                                by one for each feature below it

    """
    __tablename__="archivalook__featured_media"

    id = Column(Integer, primary_key=True, nullable=False)
    media_entry_id  = Column(Integer, ForeignKey(MediaEntry.id), nullable=False)
    media_entry = relationship(
        MediaEntry,
        backref=backref(BACKREF_NAME, uselist=False,
                        cascade="all, delete-orphan"))
    display_type = Column(Unicode, nullable=False)
    order = Column(Integer, nullable=False)

    def move_down(self):
        self.order += 1
        self.save()

    def move_up(self):
        if not self.order == 1:
            self.order -= 1
        self.save()

    def demote(self):
        if self.is_last_of_type() and self.display_type == u'primary':
            self.display_type = u'secondary'
        elif self.is_last_of_type() and self.display_type == u'secondary':
            self.display_type = u'tertiary'
        self.save()

    def promote(self):
        if self.is_first_of_type() and self.display_type == u'secondary':
            self.display_type = u'primary'
        elif self.is_first_of_type() and self.display_type == u'tertiary':
            self.display_type = u'secondary'
        self.save()

    def is_first_of_type(self):
        """
        :returns boolean                Returns True if the feature is the first
                                        of its display type to show up on the
                                        front page. Returns False otherwise.
        """
        return FeaturedMedia.query.order_by(
            FeaturedMedia.order.asc()).filter(
            FeaturedMedia.display_type==self.display_type).first() == self

    def is_last_of_type(self):
        """
        :returns boolean                Returns True if the feature is the last
                                        of its display type to show up on the
                                        front page. Returns False otherwise.
        """
        return FeaturedMedia.query.order_by(
            FeaturedMedia.order.desc()).filter(
            FeaturedMedia.display_type==self.display_type).first() == self

MODELS = [FeaturedMedia]

new_privilege_foundations = [{"privilege_name":"featurer"}]
FOUNDATIONS = {Privilege:new_privilege_foundations}
