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

import os
import Image

from mediagoblin.tools.exif import exif_fix_image_orientation, \
    extract_exif, clean_exif, get_gps_data, get_useful
from .resources import GOOD_JPG, EMPTY_JPG, BAD_JPG, GPS_JPG


def assert_in(a, b):
    assert a in b, "%r not in %r" % (a, b)


def test_exif_extraction():
    '''
    Test EXIF extraction from a good image
    '''
    result = extract_exif(GOOD_JPG)
    clean = clean_exif(result)
    useful = get_useful(clean)
    gps = get_gps_data(result)

    # Do we have the result?
    assert len(result) == 56

    # Do we have clean data?
    assert len(clean) == 53

    # GPS data?
    assert gps == {}

    # Do we have the "useful" tags?
    assert useful == {
        'EXIF Flash': {
            'field_type': 3,
            'printable': u'Flash did not fire',
            'field_offset': 380,
            'tag': 37385,
            'values': [0],
            'field_length': 2},
        'EXIF ExposureTime': {
            'field_type': 5,
            'printable': '1/125',
            'field_offset': 700,
            'tag': 33434,
            'values': [[1, 125]],
            'field_length': 8},
        'EXIF FocalLength': {
            'field_type': 5,
            'printable': '18',
            'field_offset': 780,
            'tag': 37386,
            'values': [[18, 1]],
            'field_length': 8},
        'Image Model': {
            'field_type': 2,
            'printable': 'NIKON D80',
            'field_offset': 152,
            'tag': 272,
            'values': 'NIKON D80',
            'field_length': 10},
        'Image Make': {
            'field_type': 2,
            'printable': 'NIKON CORPORATION',
            'field_offset': 134,
            'tag': 271,
            'values': 'NIKON CORPORATION',
            'field_length': 18},
        'EXIF ExposureMode': {
            'field_type': 3,
            'printable': 'Manual Exposure',
            'field_offset': 584,
            'tag': 41986,
            'values': [1],
            'field_length': 2},
        'EXIF ISOSpeedRatings': {
            'field_type': 3,
            'printable': '100',
            'field_offset': 260,
            'tag': 34855,
            'values': [100],
            'field_length': 2},
        'EXIF FNumber': {
            'field_type': 5,
            'printable': '10',
            'field_offset': 708,
            'tag': 33437,
            'values': [[10, 1]],
            'field_length': 8}}


def test_exif_image_orientation():
    '''
    Test image reorientation based on EXIF data
    '''
    result = extract_exif(GOOD_JPG)

    image = exif_fix_image_orientation(
        Image.open(GOOD_JPG),
        result)

    # Are the dimensions correct?
    assert image.size == (428, 640)

    # If this pixel looks right, the rest of the image probably will too.
    assert_in(image.getdata()[10000],
              ((41, 28, 11), (43, 27, 11))
              )


def test_exif_no_exif():
    '''
    Test an image without exif
    '''
    result = extract_exif(EMPTY_JPG)
    clean = clean_exif(result)
    useful = get_useful(clean)
    gps = get_gps_data(result)

    assert result == {}
    assert clean == {}
    assert gps == {}
    assert useful == {}


def test_exif_bad_image():
    '''
    Test EXIF extraction from a faithful, but bad image
    '''
    result = extract_exif(BAD_JPG)
    clean = clean_exif(result)
    useful = get_useful(clean)
    gps = get_gps_data(result)

    assert result == {}
    assert clean == {}
    assert gps == {}
    assert useful == {}


def test_exif_gps_data():
    '''
    Test extractiion of GPS data
    '''
    result = extract_exif(GPS_JPG)
    gps = get_gps_data(result)

    assert gps == {
        'latitude': 59.336666666666666,
        'direction': 25.674046740467404,
        'altitude': 37.64365671641791,
        'longitude': 18.016166666666667}
