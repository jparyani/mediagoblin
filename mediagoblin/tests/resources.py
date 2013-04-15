# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2013 MediaGoblin contributors.  See AUTHORS.
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


from pkg_resources import resource_filename


def resource(filename):
    return resource_filename('mediagoblin.tests', 'test_submission/' + filename)


GOOD_JPG = resource('good.jpg')
GOOD_PNG = resource('good.png')
EVIL_FILE = resource('evil')
EVIL_JPG = resource('evil.jpg')
EVIL_PNG = resource('evil.png')
BIG_BLUE = resource('bigblue.png')
GOOD_PDF = resource('good.pdf')


def resource_exif(f):
    return resource_filename('mediagoblin.tests', 'test_exif/' + f)


GOOD_JPG = resource_exif('good.jpg')
EMPTY_JPG = resource_exif('empty.jpg')
BAD_JPG = resource_exif('bad.jpg')
GPS_JPG = resource_exif('has-gps.jpg')
