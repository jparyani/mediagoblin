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
try:
    from PIL import Image
except ImportError:
    import Image

from collections import OrderedDict

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
    assert len(result) == 55

    # Do we have clean data?
    assert len(clean) == 53

    # GPS data?
    assert gps == {}

    # Do we have the "useful" tags?

    expected = OrderedDict({'EXIF CVAPattern': {'field_length': 8,
                     'field_offset': 26224,
                     'field_type': 7,
                     'printable': '[0, 2, 0, 2, 1, 2, 0, 1]',
                     'tag': 41730,
                     'values': [0, 2, 0, 2, 1, 2, 0, 1]},
 'EXIF ColorSpace': {'field_length': 2,
                     'field_offset': 476,
                     'field_type': 3,
                     'printable': 'sRGB',
                     'tag': 40961,
                     'values': [1]},
 'EXIF ComponentsConfiguration': {'field_length': 4,
                                  'field_offset': 308,
                                  'field_type': 7,
                                  'printable': 'YCbCr',
                                  'tag': 37121,
                                  'values': [1, 2, 3, 0]},
 'EXIF CompressedBitsPerPixel': {'field_length': 8,
                                 'field_offset': 756,
                                 'field_type': 5,
                                 'printable': u'4',
                                 'tag': 37122,
                                 'values': [[4, 1]]},
 'EXIF Contrast': {'field_length': 2,
                   'field_offset': 656,
                   'field_type': 3,
                   'printable': u'Soft',
                   'tag': 41992,
                   'values': [1]},
 'EXIF CustomRendered': {'field_length': 2,
                         'field_offset': 572,
                         'field_type': 3,
                         'printable': u'Normal',
                         'tag': 41985,
                         'values': [0]},
 'EXIF DateTimeDigitized': {'field_length': 20,
                            'field_offset': 736,
                            'field_type': 2,
                            'printable': u'2011:06:22 12:20:33',
                            'tag': 36868,
                            'values': u'2011:06:22 12:20:33'},
 'EXIF DateTimeOriginal': {'field_length': 20,
                           'field_offset': 716,
                           'field_type': 2,
                           'printable': u'2011:06:22 12:20:33',
                           'tag': 36867,
                           'values': u'2011:06:22 12:20:33'},
 'EXIF DigitalZoomRatio': {'field_length': 8,
                           'field_offset': 26232,
                           'field_type': 5,
                           'printable': u'1',
                           'tag': 41988,
                           'values': [[1, 1]]},
 'EXIF ExifImageLength': {'field_length': 2,
                          'field_offset': 500,
                          'field_type': 3,
                          'printable': u'2592',
                          'tag': 40963,
                          'values': [2592]},
 'EXIF ExifImageWidth': {'field_length': 2,
                         'field_offset': 488,
                         'field_type': 3,
                         'printable': u'3872',
                         'tag': 40962,
                         'values': [3872]},
 'EXIF ExifVersion': {'field_length': 4,
                      'field_offset': 272,
                      'field_type': 7,
                      'printable': u'0221',
                      'tag': 36864,
                      'values': [48, 50, 50, 49]},
 'EXIF ExposureBiasValue': {'field_length': 8,
                            'field_offset': 764,
                            'field_type': 10,
                            'printable': u'0',
                            'tag': 37380,
                            'values': [[0, 1]]},
 'EXIF ExposureMode': {'field_length': 2,
                       'field_offset': 584,
                       'field_type': 3,
                       'printable': u'Manual Exposure',
                       'tag': 41986,
                       'values': [1]},
 'EXIF ExposureProgram': {'field_length': 2,
                          'field_offset': 248,
                          'field_type': 3,
                          'printable': u'Manual',
                          'tag': 34850,
                          'values': [1]},
 'EXIF ExposureTime': {'field_length': 8,
                       'field_offset': 700,
                       'field_type': 5,
                       'printable': u'1/125',
                       'tag': 33434,
                       'values': [[1, 125]]},
 'EXIF FNumber': {'field_length': 8,
                  'field_offset': 708,
                  'field_type': 5,
                  'printable': u'10',
                  'tag': 33437,
                  'values': [[10, 1]]},
 'EXIF FileSource': {'field_length': 1,
                     'field_offset': 536,
                     'field_type': 7,
                     'printable': u'Digital Camera',
                     'tag': 41728,
                     'values': [3]},
 'EXIF Flash': {'field_length': 2,
                'field_offset': 380,
                'field_type': 3,
                'printable': u'Flash did not fire',
                'tag': 37385,
                'values': [0]},
 'EXIF FlashPixVersion': {'field_length': 4,
                          'field_offset': 464,
                          'field_type': 7,
                          'printable': u'0100',
                          'tag': 40960,
                          'values': [48, 49, 48, 48]},
 'EXIF FocalLength': {'field_length': 8,
                      'field_offset': 780,
                      'field_type': 5,
                      'printable': u'18',
                      'tag': 37386,
                      'values': [[18, 1]]},
 'EXIF FocalLengthIn35mmFilm': {'field_length': 2,
                                'field_offset': 620,
                                'field_type': 3,
                                'printable': u'27',
                                'tag': 41989,
                                'values': [27]},
 'EXIF GainControl': {'field_length': 2,
                      'field_offset': 644,
                      'field_type': 3,
                      'printable': u'None',
                      'tag': 41991,
                      'values': [0]},
 'EXIF ISOSpeedRatings': {'field_length': 2,
                          'field_offset': 260,
                          'field_type': 3,
                          'printable': u'100',
                          'tag': 34855,
                          'values': [100]},
 'EXIF InteroperabilityOffset': {'field_length': 4,
                                 'field_offset': 512,
                                 'field_type': 4,
                                 'printable': u'26240',
                                 'tag': 40965,
                                 'values': [26240]},
 'EXIF LightSource': {'field_length': 2,
                      'field_offset': 368,
                      'field_type': 3,
                      'printable': u'Unknown',
                      'tag': 37384,
                      'values': [0]},
 'EXIF MaxApertureValue': {'field_length': 8,
                           'field_offset': 772,
                           'field_type': 5,
                           'printable': u'18/5',
                           'tag': 37381,
                           'values': [[18, 5]]},
 'EXIF MeteringMode': {'field_length': 2,
                       'field_offset': 356,
                       'field_type': 3,
                       'printable': u'Pattern',
                       'tag': 37383,
                       'values': [5]},
 'EXIF Saturation': {'field_length': 2,
                     'field_offset': 668,
                     'field_type': 3,
                     'printable': u'Normal',
                     'tag': 41993,
                     'values': [0]},
 'EXIF SceneCaptureType': {'field_length': 2,
                           'field_offset': 632,
                           'field_type': 3,
                           'printable': u'Standard',
                           'tag': 41990,
                           'values': [0]},
 'EXIF SceneType': {'field_length': 1,
                    'field_offset': 548,
                    'field_type': 7,
                    'printable': u'Directly Photographed',
                    'tag': 41729,
                    'values': [1]},
 'EXIF SensingMethod': {'field_length': 2,
                        'field_offset': 524,
                        'field_type': 3,
                        'printable': u'One-chip color area',
                        'tag': 41495,
                        'values': [2]},
 'EXIF Sharpness': {'field_length': 2,
                    'field_offset': 680,
                    'field_type': 3,
                    'printable': u'Normal',
                    'tag': 41994,
                    'values': [0]},
 'EXIF SubSecTime': {'field_length': 3,
                     'field_offset': 428,
                     'field_type': 2,
                     'printable': u'10',
                     'tag': 37520,
                     'values': u'10'},
 'EXIF SubSecTimeDigitized': {'field_length': 3,
                              'field_offset': 452,
                              'field_type': 2,
                              'printable': u'10',
                              'tag': 37522,
                              'values': u'10'},
 'EXIF SubSecTimeOriginal': {'field_length': 3,
                             'field_offset': 440,
                             'field_type': 2,
                             'printable': u'10',
                             'tag': 37521,
                             'values': u'10'},
 'EXIF SubjectDistanceRange': {'field_length': 2,
                               'field_offset': 692,
                               'field_type': 3,
                               'printable': u'0',
                               'tag': 41996,
                               'values': [0]},
 'EXIF WhiteBalance': {'field_length': 2,
                       'field_offset': 596,
                       'field_type': 3,
                       'printable': u'Auto',
                       'tag': 41987,
                       'values': [0]},
 'Image DateTime': {'field_length': 20,
                    'field_offset': 194,
                    'field_type': 2,
                    'printable': u'2011:06:22 12:20:33',
                    'tag': 306,
                    'values': u'2011:06:22 12:20:33'},
 'Image ExifOffset': {'field_length': 4,
                      'field_offset': 126,
                      'field_type': 4,
                      'printable': u'214',
                      'tag': 34665,
                      'values': [214]},
 'Image Make': {'field_length': 18,
                'field_offset': 134,
                'field_type': 2,
                'printable': u'NIKON CORPORATION',
                'tag': 271,
                'values': u'NIKON CORPORATION'},
 'Image Model': {'field_length': 10,
                 'field_offset': 152,
                 'field_type': 2,
                 'printable': u'NIKON D80',
                 'tag': 272,
                 'values': u'NIKON D80'},
 'Image Orientation': {'field_length': 2,
                       'field_offset': 42,
                       'field_type': 3,
                       'printable': u'Rotated 90 CCW',
                       'tag': 274,
                       'values': [6]},
 'Image ResolutionUnit': {'field_length': 2,
                          'field_offset': 78,
                          'field_type': 3,
                          'printable': u'Pixels/Inch',
                          'tag': 296,
                          'values': [2]},
 'Image Software': {'field_length': 15,
                    'field_offset': 178,
                    'field_type': 2,
                    'printable': u'Shotwell 0.9.3',
                    'tag': 305,
                    'values': u'Shotwell 0.9.3'},
 'Image XResolution': {'field_length': 8,
                       'field_offset': 162,
                       'field_type': 5,
                       'printable': u'300',
                       'tag': 282,
                       'values': [[300, 1]]},
 'Image YCbCrPositioning': {'field_length': 2,
                            'field_offset': 114,
                            'field_type': 3,
                            'printable': u'Co-sited',
                            'tag': 531,
                            'values': [2]},
 'Image YResolution': {'field_length': 8,
                       'field_offset': 170,
                       'field_type': 5,
                       'printable': u'300',
                       'tag': 283,
                       'values': [[300, 1]]},
 'Thumbnail Compression': {'field_length': 2,
                           'field_offset': 26280,
                           'field_type': 3,
                           'printable': u'JPEG (old-style)',
                           'tag': 259,
                           'values': [6]},
 'Thumbnail ResolutionUnit': {'field_length': 2,
                              'field_offset': 26316,
                              'field_type': 3,
                              'printable': u'Pixels/Inch',
                              'tag': 296,
                              'values': [2]},
 'Thumbnail XResolution': {'field_length': 8,
                           'field_offset': 26360,
                           'field_type': 5,
                           'printable': u'300',
                           'tag': 282,
                           'values': [[300, 1]]},
 'Thumbnail YCbCrPositioning': {'field_length': 2,
                                'field_offset': 26352,
                                'field_type': 3,
                                'printable': u'Co-sited',
                                'tag': 531,
                                'values': [2]},
 'Thumbnail YResolution': {'field_length': 8,
                           'field_offset': 26368,
                           'field_type': 5,
                           'printable': u'300',
                           'tag': 283,
                           'values': [[300, 1]]}})

    for k, v in useful.items():
        assert v == expected[k]


def test_exif_image_orientation():
    '''
    Test image reorientation based on EXIF data
    '''
    result = extract_exif(GOOD_JPG)

    image = exif_fix_image_orientation(
        Image.open(GOOD_JPG),
        result)

    # Are the dimensions correct?
    assert image.size in ((428, 640), (640, 428))

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
