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

from mediagoblin.tools.extlib.EXIF import process_file, Ratio
from mediagoblin.processing import BadMediaFail
from mediagoblin.tools.translate import pass_to_ugettext as _

# A list of tags that should be stored for faster access
USEFUL_TAGS = [
    'Image Make',
    'Image Model',
    'EXIF FNumber',
    'EXIF Flash',
    'EXIF FocalLength',
    'EXIF ExposureTime',
    'EXIF ApertureValue',
    'EXIF ExposureMode',
    'EXIF ISOSpeedRatings',
    'EXIF UserComment',
    ]

def exif_fix_image_orientation(im, exif_tags):
    """
    Translate any EXIF orientation to raw orientation

    Cons:
    - REDUCES IMAGE QUALITY by recompressig it

    Pros:
    - Cures my neck pain
    """
    # Rotate image
    if 'Image Orientation' in exif_tags:
        rotation_map = {
            3: 180,
            6: 270,
            8: 90}
        orientation = exif_tags['Image Orientation'].values[0]
        if orientation in rotation_map.keys():
            im = im.rotate(
                rotation_map[orientation])

    return im

def extract_exif(filename):
    """
    Returns EXIF tags found in file at ``filename``
    """
    exif_tags = {}

    try:
        image = open(filename)
        exif_tags = process_file(image)
    except IOError:
        raise BadMediaFail(_('Could not read the image file.'))

    return exif_tags

def clean_exif(exif):
    '''
    Clean the result from anything the database cannot handle
    '''
    # Discard any JPEG thumbnail, for database compatibility
    # and that I cannot see a case when we would use it.
    # It takes up some space too.
    disabled_tags = [
        'Thumbnail JPEGInterchangeFormatLength',
        'JPEGThumbnail',
        'Thumbnail JPEGInterchangeFormat']

    clean_exif = {}

    for key, value in exif.items():
        if not key in disabled_tags:
            clean_exif[key] = _ifd_tag_to_dict(value)

    return clean_exif

def _ifd_tag_to_dict(tag):
    data = {
        'printable': tag.printable,
        'tag': tag.tag,
        'field_type': tag.field_type,
        'field_offset': tag.field_offset,
        'field_length': tag.field_length,
        'values': None}
    if type(tag.values) == list:
        data['values'] = []
        for val in tag.values:
            if isinstance(val, Ratio):
                data['values'].append(
                    _ratio_to_list(val))
            else:
                data['values'].append(val)
    else:
        data['values'] = tag.values

    return data

def _ratio_to_list(ratio):
    return [ratio.num, ratio.den]

def get_useful(tags):
    useful = {}
    for key, tag in tags.items():
        if key in USEFUL_TAGS:
            useful[key] = tag

    return useful
            

def get_gps_data(tags):
    """
    Processes EXIF data returned by EXIF.py
    """
    gps_data = {}

    if not 'Image GPSInfo' in tags:
        return gps_data

    try:
        dms_data = {
            'latitude': tags['GPS GPSLatitude'],
            'longitude': tags['GPS GPSLongitude']}

        for key, dat in dms_data.items():
            gps_data[key] = (
                lambda v:
                    float(v[0].num) / float(v[0].den) \
                    + (float(v[1].num) / float(v[1].den) / 60 )\
                    + (float(v[2].num) / float(v[2].den) / (60 * 60))
                )(dat.values)
    except KeyError:
        pass

    try:
        gps_data['direction'] = (
            lambda d:
                float(d.num) / float(d.den)
            )(tags['GPS GPSImgDirection'].values[0])
    except KeyError:
        pass

    try:
        gps_data['altitude'] = (
            lambda a:
                float(a.num) / float(a.den)
            )(tags['GPS GPSAltitude'].values[0])
    except KeyError:
        pass

    return gps_data
