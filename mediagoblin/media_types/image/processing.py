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

import Image
import os
import logging

from mediagoblin import mg_globals as mgg
from mediagoblin.processing import BadMediaFail, \
    create_pub_filepath, FilenameBuilder
from mediagoblin.tools.exif import exif_fix_image_orientation, \
    extract_exif, clean_exif, get_gps_data, get_useful, \
    exif_image_needs_rotation

_log = logging.getLogger(__name__)

PIL_FILTERS = {
    'NEAREST': Image.NEAREST,
    'BILINEAR': Image.BILINEAR,
    'BICUBIC': Image.BICUBIC,
    'ANTIALIAS': Image.ANTIALIAS}


def resize_image(entry, filename, new_path, exif_tags, workdir, new_size,
                 size_limits=(0, 0)):
    """
    Store a resized version of an image and return its pathname.

    Arguments:
    entry -- the entry for the image to resize
    filename -- the filename of the original image being resized
    new_path -- public file path for the new resized image
    exif_tags -- EXIF data for the original image
    workdir -- directory path for storing converted image files
    new_size -- 2-tuple size for the resized image
    """
    try:
        resized = Image.open(filename)
    except IOError:
        raise BadMediaFail()
    resized = exif_fix_image_orientation(resized, exif_tags)  # Fix orientation

    filter_config = \
            mgg.global_config['media_type:mediagoblin.media_types.image']\
                ['resize_filter']

    try:
        resize_filter = PIL_FILTERS[filter_config.upper()]
    except KeyError:
        raise Exception('Filter "{0}" not found, choose one of {1}'.format(
            unicode(filter_config),
            u', '.join(PIL_FILTERS.keys())))

    resized.thumbnail(new_size, resize_filter)

    # Copy the new file to the conversion subdir, then remotely.
    tmp_resized_filename = os.path.join(workdir, new_path[-1])
    with file(tmp_resized_filename, 'w') as resized_file:
        resized.save(resized_file)
    mgg.public_store.copy_local_to_storage(tmp_resized_filename, new_path)


SUPPORTED_FILETYPES = ['png', 'gif', 'jpg', 'jpeg']


def sniff_handler(media_file, **kw):
    if kw.get('media') is not None:  # That's a double negative!
        name, ext = os.path.splitext(kw['media'].filename)
        clean_ext = ext[1:].lower()  # Strip the . from ext and make lowercase

        if clean_ext in SUPPORTED_FILETYPES:
            _log.info('Found file extension in supported filetypes')
            return True
        else:
            _log.debug('Media present, extension not found in {0}'.format(
                    SUPPORTED_FILETYPES))
    else:
        _log.warning('Need additional information (keyword argument \'media\')'
                     ' to be able to handle sniffing')

    return False


def process_image(proc_state):
    """Code to process an image. Will be run by celery.

    A Workbench() represents a local tempory dir. It is automatically
    cleaned up when this function exits.
    """
    entry = proc_state.entry
    workbench = proc_state.workbench

    # Conversions subdirectory to avoid collisions
    conversions_subdir = os.path.join(
        workbench.dir, 'conversions')
    os.mkdir(conversions_subdir)

    queued_filename = proc_state.get_queued_filename()
    name_builder = FilenameBuilder(queued_filename)

    # EXIF extraction
    exif_tags = extract_exif(queued_filename)
    gps_data = get_gps_data(exif_tags)

    # Always create a small thumbnail
    thumb_filepath = create_pub_filepath(
        entry, name_builder.fill('{basename}.thumbnail{ext}'))
    resize_image(entry, queued_filename, thumb_filepath,
                exif_tags, conversions_subdir,
                (mgg.global_config['media:thumb']['max_width'],
                 mgg.global_config['media:thumb']['max_height']))
    entry.media_files[u'thumb'] = thumb_filepath

    # If the size of the original file exceeds the specified size of a `medium`
    # file, a `.medium.jpg` files is created and later associated with the media
    # entry.
    medium = Image.open(queued_filename)
    if medium.size[0] > mgg.global_config['media:medium']['max_width'] \
        or medium.size[1] > mgg.global_config['media:medium']['max_height'] \
        or exif_image_needs_rotation(exif_tags):
        medium_filepath = create_pub_filepath(
            entry, name_builder.fill('{basename}.medium{ext}'))
        resize_image(
            entry, queued_filename, medium_filepath,
            exif_tags, conversions_subdir,
            (mgg.global_config['media:medium']['max_width'],
             mgg.global_config['media:medium']['max_height']))
        entry.media_files[u'medium'] = medium_filepath

    # Copy our queued local workbench to its final destination
    proc_state.copy_original(name_builder.fill('{basename}{ext}'))

    # Remove queued media file from storage and database
    proc_state.delete_queue_file()

    # Insert exif data into database
    exif_all = clean_exif(exif_tags)

    if len(exif_all):
        entry.media_data_init(exif_all=exif_all)

    if len(gps_data):
        for key in list(gps_data.keys()):
            gps_data['gps_' + key] = gps_data.pop(key)
        entry.media_data_init(**gps_data)


if __name__ == '__main__':
    import sys
    import pprint

    pp = pprint.PrettyPrinter()

    result = extract_exif(sys.argv[1])
    gps = get_gps_data(result)
    clean = clean_exif(result)
    useful = get_useful(clean)

    print pp.pprint(
        clean)
