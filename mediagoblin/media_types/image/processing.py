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

try:
    from PIL import Image
except ImportError:
    import Image
import os
import logging
import argparse

from mediagoblin import mg_globals as mgg
from mediagoblin.processing import (
    BadMediaFail, FilenameBuilder,
    MediaProcessor, ProcessingManager,
    request_from_args, get_process_filename,
    store_public, copy_original)
from mediagoblin.tools.exif import exif_fix_image_orientation, \
    extract_exif, clean_exif, get_gps_data, get_useful, \
    exif_image_needs_rotation

_log = logging.getLogger(__name__)

PIL_FILTERS = {
    'NEAREST': Image.NEAREST,
    'BILINEAR': Image.BILINEAR,
    'BICUBIC': Image.BICUBIC,
    'ANTIALIAS': Image.ANTIALIAS}

MEDIA_TYPE = 'mediagoblin.media_types.image'


def resize_image(entry, resized, keyname, target_name, new_size,
                 exif_tags, workdir, quality, filter):
    """
    Store a resized version of an image and return its pathname.

    Arguments:
    proc_state -- the processing state for the image to resize
    resized -- an image from Image.open() of the original image being resized
    keyname -- Under what key to save in the db.
    target_name -- public file path for the new resized image
    exif_tags -- EXIF data for the original image
    workdir -- directory path for storing converted image files
    new_size -- 2-tuple size for the resized image
    quality -- level of compression used when resizing images
    filter -- One of BICUBIC, BILINEAR, NEAREST, ANTIALIAS
    """
    resized = exif_fix_image_orientation(resized, exif_tags)  # Fix orientation

    try:
        resize_filter = PIL_FILTERS[filter.upper()]
    except KeyError:
        raise Exception('Filter "{0}" not found, choose one of {1}'.format(
            unicode(filter),
            u', '.join(PIL_FILTERS.keys())))

    resized.thumbnail(new_size, resize_filter)

    # Copy the new file to the conversion subdir, then remotely.
    tmp_resized_filename = os.path.join(workdir, target_name)
    with file(tmp_resized_filename, 'w') as resized_file:
        resized.save(resized_file, quality=quality)
    store_public(entry, keyname, tmp_resized_filename, target_name)

    # store the thumb/medium info
    image_info = {'width': new_size[0],
                  'height': new_size[1],
                  'quality': quality,
                  'filter': filter}

    entry.set_file_metadata(keyname, **image_info)


def resize_tool(entry,
                force, keyname, orig_file, target_name,
                conversions_subdir, exif_tags, quality, filter, new_size=None):
    # Use the default size if new_size was not given
    if not new_size:
        max_width = mgg.global_config['media:' + keyname]['max_width']
        max_height = mgg.global_config['media:' + keyname]['max_height']
        new_size = (max_width, max_height)

    # If thumb or medium is already the same quality and size, then don't
    # reprocess
    if _skip_resizing(entry, keyname, new_size, quality, filter):
        _log.info('{0} of same size and quality already in use, skipping '
                  'resizing of media {1}.'.format(keyname, entry.id))
        return

    # If the size of the original file exceeds the specified size for the desized
    # file, a target_name file is created and later associated with the media
    # entry.
    # Also created if the file needs rotation, or if forced.
    try:
        im = Image.open(orig_file)
    except IOError:
        raise BadMediaFail()
    if force \
        or im.size[0] > new_size[0]\
        or im.size[1] > new_size[1]\
        or exif_image_needs_rotation(exif_tags):
        resize_image(
            entry, im, unicode(keyname), target_name,
            tuple(new_size),
            exif_tags, conversions_subdir,
            quality, filter)


def _skip_resizing(entry, keyname, size, quality, filter):
    """
    Determines wither the saved thumb or medium is of the same quality and size
    """
    image_info = entry.get_file_metadata(keyname)

    if not image_info:
        return False

    skip = True

    if image_info.get('width') != size[0]:
        skip = False

    elif image_info.get('height') != size[1]:
        skip = False

    elif image_info.get('filter') != filter:
        skip = False

    elif image_info.get('quality') != quality:
        skip = False

    return skip


SUPPORTED_FILETYPES = ['png', 'gif', 'jpg', 'jpeg', 'tiff']


def sniff_handler(media_file, filename):
    _log.info('Sniffing {0}'.format(MEDIA_TYPE))
    name, ext = os.path.splitext(filename)
    clean_ext = ext[1:].lower()  # Strip the . from ext and make lowercase

    if clean_ext in SUPPORTED_FILETYPES:
        _log.info('Found file extension in supported filetypes')
        return MEDIA_TYPE
    else:
        _log.debug('Media present, extension not found in {0}'.format(
                SUPPORTED_FILETYPES))

    return None


class CommonImageProcessor(MediaProcessor):
    """
    Provides a base for various media processing steps
    """
    # list of acceptable file keys in order of prefrence for reprocessing
    acceptable_files = ['original', 'medium']

    def common_setup(self):
        """
        Set up the workbench directory and pull down the original file
        """
        self.image_config = mgg.global_config['plugins'][
            'mediagoblin.media_types.image']

        ## @@: Should this be two functions?
        # Conversions subdirectory to avoid collisions
        self.conversions_subdir = os.path.join(
            self.workbench.dir, 'conversions')
        os.mkdir(self.conversions_subdir)

        # Pull down and set up the processing file
        self.process_filename = get_process_filename(
            self.entry, self.workbench, self.acceptable_files)
        self.name_builder = FilenameBuilder(self.process_filename)

        # Exif extraction
        self.exif_tags = extract_exif(self.process_filename)

    def generate_medium_if_applicable(self, size=None, quality=None,
                                      filter=None):
        if not quality:
            quality = self.image_config['quality']
        if not filter:
            filter = self.image_config['resize_filter']

        resize_tool(self.entry, False, 'medium', self.process_filename,
                    self.name_builder.fill('{basename}.medium{ext}'),
                    self.conversions_subdir, self.exif_tags, quality,
                    filter, size)

    def generate_thumb(self, size=None, quality=None, filter=None):
        if not quality:
            quality = self.image_config['quality']
        if not filter:
            filter = self.image_config['resize_filter']

        resize_tool(self.entry, True, 'thumb', self.process_filename,
                    self.name_builder.fill('{basename}.thumbnail{ext}'),
                    self.conversions_subdir, self.exif_tags, quality,
                    filter, size)

    def copy_original(self):
        copy_original(
            self.entry, self.process_filename,
            self.name_builder.fill('{basename}{ext}'))

    def extract_metadata(self):
        # Is there any GPS data
        gps_data = get_gps_data(self.exif_tags)

        # Insert exif data into database
        exif_all = clean_exif(self.exif_tags)

        if len(exif_all):
            self.entry.media_data_init(exif_all=exif_all)

        if len(gps_data):
            for key in list(gps_data.keys()):
                gps_data['gps_' + key] = gps_data.pop(key)
            self.entry.media_data_init(**gps_data)


class InitialProcessor(CommonImageProcessor):
    """
    Initial processing step for new images
    """
    name = "initial"
    description = "Initial processing"

    @classmethod
    def media_is_eligible(cls, entry=None, state=None):
        """
        Determine if this media type is eligible for processing
        """
        if not state:
            state = entry.state
        return state in (
            "unprocessed", "failed")

    ###############################
    # Command line interface things
    ###############################

    @classmethod
    def generate_parser(cls):
        parser = argparse.ArgumentParser(
            description=cls.description,
            prog=cls.name)

        parser.add_argument(
            '--size',
            nargs=2,
            metavar=('max_width', 'max_height'),
            type=int)

        parser.add_argument(
            '--thumb-size',
            nargs=2,
            metavar=('max_width', 'max_height'),
            type=int)

        parser.add_argument(
            '--filter',
            choices=['BICUBIC', 'BILINEAR', 'NEAREST', 'ANTIALIAS'])

        parser.add_argument(
            '--quality',
            type=int,
            help='level of compression used when resizing images')

        return parser

    @classmethod
    def args_to_request(cls, args):
        return request_from_args(
            args, ['size', 'thumb_size', 'filter', 'quality'])

    def process(self, size=None, thumb_size=None, quality=None, filter=None):
        self.common_setup()
        self.generate_medium_if_applicable(size=size, filter=filter,
                                           quality=quality)
        self.generate_thumb(size=thumb_size, filter=filter, quality=quality)
        self.copy_original()
        self.extract_metadata()
        self.delete_queue_file()


class Resizer(CommonImageProcessor):
    """
    Resizing process steps for processed media
    """
    name = 'resize'
    description = 'Resize image'
    thumb_size = 'size'

    @classmethod
    def media_is_eligible(cls, entry=None, state=None):
        """
        Determine if this media type is eligible for processing
        """
        if not state:
            state = entry.state
        return state in 'processed'

    ###############################
    # Command line interface things
    ###############################

    @classmethod
    def generate_parser(cls):
        parser = argparse.ArgumentParser(
            description=cls.description,
            prog=cls.name)

        parser.add_argument(
            '--size',
            nargs=2,
            metavar=('max_width', 'max_height'),
            type=int)

        parser.add_argument(
            '--filter',
            choices=['BICUBIC', 'BILINEAR', 'NEAREST', 'ANTIALIAS'])

        parser.add_argument(
            '--quality',
            type=int,
            help='level of compression used when resizing images')

        parser.add_argument(
            'file',
            choices=['medium', 'thumb'])

        return parser

    @classmethod
    def args_to_request(cls, args):
        return request_from_args(
            args, ['size', 'file', 'quality', 'filter'])

    def process(self, file, size=None, filter=None, quality=None):
        self.common_setup()
        if file == 'medium':
            self.generate_medium_if_applicable(size=size, filter=filter,
                                              quality=quality)
        elif file == 'thumb':
            self.generate_thumb(size=size, filter=filter, quality=quality)


class ImageProcessingManager(ProcessingManager):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.add_processor(InitialProcessor)
        self.add_processor(Resizer)


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
