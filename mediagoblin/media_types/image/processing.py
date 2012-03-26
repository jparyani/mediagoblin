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

from mediagoblin import mg_globals as mgg
from mediagoblin.processing import BadMediaFail, \
    create_pub_filepath, THUMB_SIZE, MEDIUM_SIZE, FilenameBuilder
from mediagoblin.tools.exif import exif_fix_image_orientation, \
    extract_exif, clean_exif, get_gps_data, get_useful

def resize_image(entry, filename, new_path, exif_tags, workdir, new_size,
                 size_limits=(0, 0)):
    """Store a resized version of an image and return its pathname.

    Arguments:
    entry -- the entry for the image to resize
    filename -- the filename of the original image being resized
    new_path -- public file path for the new resized image
    exif_tags -- EXIF data for the original image
    workdir -- directory path for storing converted image files
    new_size -- 2-tuple size for the resized image
    size_limits (optional) -- image is only resized if it exceeds this size

    """
    try:
        resized = Image.open(filename)
    except IOError:
        raise BadMediaFail()
    resized = exif_fix_image_orientation(resized, exif_tags)  # Fix orientation

    if ((resized.size[0] > size_limits[0]) or
        (resized.size[1] > size_limits[1])):
        resized.thumbnail(new_size, Image.ANTIALIAS)

    # Copy the new file to the conversion subdir, then remotely.
    tmp_resized_filename = os.path.join(workdir, new_path[-1])
    with file(tmp_resized_filename, 'w') as resized_file:
        resized.save(resized_file)
    mgg.public_store.copy_local_to_storage(tmp_resized_filename, new_path)

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
    name_builder = FilenameBuilder(queued_filename)

    # EXIF extraction
    exif_tags = extract_exif(queued_filename)
    gps_data = get_gps_data(exif_tags)

    # Always create a small thumbnail
    thumb_filepath = create_pub_filepath(
        entry, name_builder.fill('{basename}.thumbnail{ext}'))
    resize_image(entry, queued_filename, thumb_filepath,
                 exif_tags, conversions_subdir, THUMB_SIZE)

    # If the size of the original file exceeds the specified size of a `medium`
    # file, a `.medium.jpg` files is created and later associated with the media
    # entry.
    medium_filepath = create_pub_filepath(
        entry, name_builder.fill('{basename}.medium{ext}'))
    resize_image(entry, queued_filename, medium_filepath,
                 exif_tags, conversions_subdir, MEDIUM_SIZE, MEDIUM_SIZE)

    # we have to re-read because unlike PIL, not everything reads
    # things in string representation :)
    queued_file = file(queued_filename, 'rb')

    with queued_file:
        original_filepath = create_pub_filepath(
            entry, name_builder.fill('{basename}{ext}') )

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
    exif_all = clean_exif(exif_tags)

    if len(exif_all):
        entry.media_data_init(exif_all=exif_all)

    if len(gps_data):
        for key in list(gps_data.keys()):
            gps_data['gps_' + key] = gps_data.pop(key)
        entry.media_data_init(**gps_data)

    # clean up workbench
    workbench.destroy_self()

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
