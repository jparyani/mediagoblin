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

import Image
import os

from mediagoblin import mg_globals as mgg
from mediagoblin.processing import BadMediaFail, \
    create_pub_filepath, THUMB_SIZE, MEDIUM_SIZE
from mediagoblin.media_types.image.EXIF import process_file
from mediagoblin.tools.translate import pass_to_ugettext as _

def process_image(entry):
    """
    Code to process an image
    """
    workbench = mgg.workbench_manager.create_workbench()
    # Conversions subdirectory to avoid collisions
    conversions_subdir = os.path.join(
        workbench.dir, 'conversions')
    os.mkdir(conversions_subdir)

    queued_filepath = entry.queued_media_file
    queued_filename = workbench.localized_file(
        mgg.queue_store, queued_filepath,
        'source')

    filename_bits = os.path.splitext(queued_filename)
    basename = os.path.split(filename_bits[0])[1]
    extension = filename_bits[1].lower()

    # EXIF extraction
    exif_tags = extract_exif(queued_filename)
    gps_data = get_gps_data(exif_tags)

    try:
        thumb = Image.open(queued_filename)
    except IOError:
        raise BadMediaFail()

    thumb = exif_fix_image_orientation(thumb, exif_tags)

    thumb.thumbnail(THUMB_SIZE, Image.ANTIALIAS)

    # Copy the thumb to the conversion subdir, then remotely.
    thumb_filename = 'thumbnail' + extension
    thumb_filepath = create_pub_filepath(entry, thumb_filename)
    tmp_thumb_filename = os.path.join(
        conversions_subdir, thumb_filename)
    with file(tmp_thumb_filename, 'w') as thumb_file:
        thumb.save(thumb_file)
    mgg.public_store.copy_local_to_storage(
        tmp_thumb_filename, thumb_filepath)

    # If the size of the original file exceeds the specified size of a `medium`
    # file, a `medium.jpg` files is created and later associated with the media
    # entry.
    medium = Image.open(queued_filename)
    # Fox orientation
    medium = exif_fix_image_orientation(medium, exif_tags)

    if medium.size[0] > MEDIUM_SIZE[0] or medium.size[1] > MEDIUM_SIZE[1]:
        medium.thumbnail(MEDIUM_SIZE, Image.ANTIALIAS)

    medium_filename = 'medium' + extension
    medium_filepath = create_pub_filepath(entry, medium_filename)
    tmp_medium_filename = os.path.join(
        conversions_subdir, medium_filename)

    with file(tmp_medium_filename, 'w') as medium_file:
        medium.save(medium_file)

    mgg.public_store.copy_local_to_storage(
        tmp_medium_filename, medium_filepath)

    # we have to re-read because unlike PIL, not everything reads
    # things in string representation :)
    queued_file = file(queued_filename, 'rb')

    with queued_file:
        #create_pub_filepath(entry, queued_filepath[-1])
        original_filepath = create_pub_filepath(entry, basename + extension) 

        with mgg.public_store.get_file(original_filepath, 'wb') \
            as original_file:
            original_file.write(queued_file.read())

    # Remove queued media file from storage and database
    mgg.queue_store.delete_file(queued_filepath)
    entry.queued_media_file = []

    # Insert media file information into database
    media_files_dict = entry.setdefault('media_files', {})
    media_files_dict['thumb'] = thumb_filepath
    media_files_dict['original'] = original_filepath
    media_files_dict['medium'] = medium_filepath

    # Insert exif data into database
    media_data = entry.setdefault('media_data', {})
    media_data['exif'] = clean_exif(exif_tags)
    media_data['gps'] = gps_data

    # clean up workbench
    workbench.destroy_self()

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
        BadMediaFail(_('Could not read the image file.'))

    return exif_tags

def clean_exif(exif):
    # Clean the result from anything the database cannot handle

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
            clean_exif[key] = str(value)

    return clean_exif
    

def get_gps_data(exif):
    """
    Processes EXIF data returned by EXIF.py
    """
    if not 'Image GPSInfo' in exif:
        return False

    gps_data = {}

    try:
        dms_data = {
            'latitude': exif['GPS GPSLatitude'],
            'longitude': exif['GPS GPSLongitude']}

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
            )(exif['GPS GPSImgDirection'].values[0])
    except KeyError:
        pass

    try:
        gps_data['altitude'] = (
            lambda a:
                float(a.num) / float(a.den)
            )(exif['GPS GPSAltitude'].values[0])
    except KeyError:
        pass

    return gps_data


if __name__ == '__main__':
    import sys
    import pprint

    pp = pprint.PrettyPrinter()

    result = extract_exif(sys.argv[1])
    gps = get_gps_data(result)

    import pdb
    pdb.set_trace()

    print pp.pprint(
        result)
