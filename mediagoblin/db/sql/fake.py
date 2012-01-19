# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011,2012 MediaGoblin contributors.  See AUTHORS.
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


"""
This module contains some fake classes and functions to
calm the rest of the code base. Or provide super minimal
implementations.

Currently:
- ObjectId "class": It's a function mostly doing
  int(init_arg) to convert string primary keys into
  integer primary keys.
- InvalidId exception
- DESCENDING "constant"
"""


DESCENDING = object()  # a unique object for this "constant"


class InvalidId(Exception):
    pass


def ObjectId(value=None):
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        raise InvalidId("%r is an invalid id" % value)
