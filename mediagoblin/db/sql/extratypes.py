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


from sqlalchemy.types import TypeDecorator, Unicode


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
