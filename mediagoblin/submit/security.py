# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 Free Software Foundation, Inc
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

from mimetypes import guess_type

from Image import open as image_open

ALLOWED = ['image/jpeg', 'image/png', 'image/tiff', 'image/gif']

def check_filetype(posted_file):
    if not guess_type(posted_file.filename) in ALLOWED:
        return False

    try:
        image = image_open(posted_file.file)
    except IOError:
        return False

    return True
