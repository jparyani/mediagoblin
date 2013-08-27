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


from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.types import TypeDecorator, Unicode, TEXT
import json


class PathTupleWithSlashes(TypeDecorator):
    "Represents a Tuple of strings as a slash separated string."

    impl = Unicode

    def process_bind_param(self, value, dialect):
        if value is not None:
            if len(value) == 0:
                value = None
            else:
                value = '/'.join(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = tuple(value.split('/'))
        return value


# The following  two classes and only these two classes is in very
# large parts based on example code from sqlalchemy.
#
# The original copyright notice and license follows:
#     Copyright (C) 2005-2011 the SQLAlchemy authors and contributors <see AUTHORS file>
#
#     This module is part of SQLAlchemy and is released under
#     the MIT License: http://www.opensource.org/licenses/mit-license.php
#
class JSONEncoded(TypeDecorator):
    "Represents an immutable structure as a json-encoded string."

    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class MutationDict(Mutable, dict):
    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to MutationDict."

        if not isinstance(value, MutationDict):
            if isinstance(value, dict):
                return MutationDict(value)

            # this call will raise ValueError
            return Mutable.coerce(key, value)
        else:
            return value

    def __setitem__(self, key, value):
        "Detect dictionary set events and emit change events."

        dict.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        "Detect dictionary del events and emit change events."

        dict.__delitem__(self, key)
        self.changed()
