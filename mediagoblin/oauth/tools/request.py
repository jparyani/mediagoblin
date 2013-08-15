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

def decode_authorization_header(header):
    """ Decodes a HTTP Authorization Header to python dictionary """
    authorization = header.get("Authorization", "").lstrip(" ").lstrip("OAuth")
    tokens = {}

    for param in authorization.split(","):
        try:
            key, value = param.split("=")
        except ValueError:
            continue
 
        key = key.lstrip(" ")
        value = value.lstrip(" ").lstrip('"')
        value = value.rstrip(" ").rstrip('"')

        tokens[key] = value

    return tokens

