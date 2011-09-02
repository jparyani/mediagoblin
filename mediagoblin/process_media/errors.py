# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 MediaGoblin contributors.  See AUTHORS.
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

from mediagoblin.util import lazy_pass_to_ugettext as _

class BaseProcessingFail(Exception):
    """
    Base exception that all other processing failure messages should
    subclass from.
  
    You shouldn't call this itself; instead you should subclass it
    and provid the exception_path and general_message applicable to
    this error.
    """
    general_message = u''
  
    @property
    def exception_path(self):
        return u"%s:%s" % (
            self.__class__.__module__, self.__class__.__name__)

    def __init__(self, **metadata):
        self.metadata = metadata or {}
  
  
class BadMediaFail(BaseProcessingFail):
    """
    Error that should be raised when an inappropriate file was given
    for the media type specified.
    """
    general_message = _(u'Invalid file given for media type.')
