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
from mediagoblin.db.models import MediaEntry
from mediagoblin.processing import (
    BadMediaFail, FilenameBuilder,
    MediaProcessor, ProcessingManager)
from mediagoblin.submit.lib import run_process_media
from mediagoblin.tools.exif import exif_fix_image_orientation, \
    extract_exif, clean_exif, get_gps_data, get_useful, \
    exif_image_needs_rotation
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _

_log = logging.getLogger(__name__)

PIL_FILTERS = {
    'NEAREST': Image.NEAREST,
    'BILINEAR': Image.BILINEAR,
    'BICUBIC': Image.BICUBIC,
    'ANTIALIAS': Image.ANTIALIAS}

MEDIA_TYPE = 'mediagoblin.media_types.image'


def resize_image(proc_state, resized, keyname, target_name, new_size,
                 exif_tags, workdir):
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
    """
    config = mgg.global_config['media_type:mediagoblin.media_types.image']

    resized = exif_fix_image_orientation(resized, exif_tags)  # Fix orientation

    filter_config = config['resize_filter']
    try:
        resize_filter = PIL_FILTERS[filter_config.upper()]
    except KeyError:
        raise Exception('Filter "{0}" not found, choose one of {1}'.format(
            unicode(filter_config),
            u', '.join(PIL_FILTERS.keys())))

    resized.thumbnail(new_size, resize_filter)

    # Copy the new file to the conversion subdir, then remotely.
    tmp_resized_filename = os.path.join(workdir, target_name)
    with file(tmp_resized_filename, 'w') as resized_file:
        resized.save(resized_file, quality=config['quality'])
    proc_state.store_public(keyname, tmp_resized_filename, target_name)


def resize_tool(proc_state, force, keyname, target_name,
                conversions_subdir, exif_tags, new_size=None):
    # filename -- the filename of the original image being resized
    filename = proc_state.get_orig_filename()

    # Use the default size if new_size was not given
    if not new_size:
        max_width = mgg.global_config['media:' + keyname]['max_width']
        max_height = mgg.global_config['media:' + keyname]['max_height']
        new_size = (max_width, max_height)

    # If the size of the original file exceeds the specified size for the desized
    # file, a target_name file is created and later associated with the media
    # entry.
    # Also created if the file needs rotation, or if forced.
    try:
        im = Image.open(filename)
    except IOError:
        raise BadMediaFail()
    if force \
        or im.size[0] > new_size[0]\
        or im.size[1] > new_size[1]\
        or exif_image_needs_rotation(exif_tags):
        resize_image(
            proc_state, im, unicode(keyname), target_name,
            new_size,
            exif_tags, conversions_subdir)


SUPPORTED_FILETYPES = ['png', 'gif', 'jpg', 'jpeg', 'tiff']


def sniff_handler(media_file, **kw):
    _log.info('Sniffing {0}'.format(MEDIA_TYPE))
    if kw.get('media') is not None:  # That's a double negative!
        name, ext = os.path.splitext(kw['media'].filename)
        clean_ext = ext[1:].lower()  # Strip the . from ext and make lowercase

        if clean_ext in SUPPORTED_FILETYPES:
            _log.info('Found file extension in supported filetypes')
            return MEDIA_TYPE
        else:
            _log.debug('Media present, extension not found in {0}'.format(
                    SUPPORTED_FILETYPES))
    else:
        _log.warning('Need additional information (keyword argument \'media\')'
                     ' to be able to handle sniffing')

    return None


class ProcessImage(object):
    """Code to process an image. Will be run by celery.

    A Workbench() represents a local tempory dir. It is automatically
    cleaned up when this function exits.
    """
    def __init__(self, proc_state=None):
        if proc_state:
            self.proc_state = proc_state
            self.entry = proc_state.entry
            self.workbench = proc_state.workbench

            # Conversions subdirectory to avoid collisions
            self.conversions_subdir = os.path.join(
                self.workbench.dir, 'convirsions')

            self.orig_filename = proc_state.get_orig_filename()
            self.name_builder = FilenameBuilder(self.orig_filename)

            # Exif extraction
            self.exif_tags = extract_exif(self.orig_filename)

            os.mkdir(self.conversions_subdir)

    def reprocess_action(self, args):
        """
        List the available actions for media in a given state
        """
        if args[0].state == 'processed':
            print _('\n Available reprocessing actions for processed images:'
                    '\n \t --resize: thumb or medium'
                    '\n Options:'
                    '\n \t --size: max_width max_height (defaults to'
                    'config specs)')
            return True

    def _parser(self, args):
        """
        Parses the unknown args from the gmg parser
        """
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '--resize',
            choices=['thumb', 'medium'])
        parser.add_argument(
            '--size',
            nargs=2,
            metavar=('max_width', 'max_height'),
            type=int)
        parser.add_argument(
            '--initial_processing',
            action='store_true')

        return parser.parse_args(args[1])

    def _check_eligible(self, entry_args, reprocess_args):
        """
        Check to see if we can actually process the given media as requested
        """

        if entry_args.state == 'processed':
            if reprocess_args.initial_processing:
                raise Exception(_('You can not run --initial_processing on'
                                  ' media that has already been processed.'))

        if entry_args.state == 'failed':
            if reprocess_args.resize:
                raise Exception(_('You can not run --resize on media that has'
                                  ' not been processed.'))
            if reprocess_args.size:
                _log.warn('With --initial_processing, the --size flag will be'
                          ' ignored.')

        if entry_args.state == 'processing':
            raise Exception(_('We currently do not support reprocessing on'
                              ' media that is in the "processing" state.'))

    def initial_processing(self):
        # Is there any GPS data
        gps_data = get_gps_data(self.exif_tags)

         # Always create a small thumbnail
        resize_tool(self.proc_state, True, 'thumb', self.orig_filename,
                    self.name_builder.fill('{basename}.thumbnail{ext}'),
                    self.conversions_subdir, self.exif_tags)

        # Possibly create a medium
        resize_tool(self.proc_state, False, 'medium', self.orig_filename,
                    self.name_builder.fill('{basename}.medium{ext}'),
                    self.conversions_subdir, self.exif_tags)

        # Copy our queued local workbench to its final destination
        self.proc_state.copy_original(self.name_builder.fill('{basename}{ext}'))

        # Remove queued media file from storage and database
        self.proc_state.delete_queue_file()

        # Insert exif data into database
        exif_all = clean_exif(self.exif_tags)

        if len(exif_all):
            self.entry.media_data_init(exif_all=exif_all)

        if len(gps_data):
            for key in list(gps_data.keys()):
                gps_data['gps_' + key] = gps_data.pop(key)
            self.entry.media_data_init(**gps_data)

    def reprocess(self, reprocess_info):
        """
        This function actually does the reprocessing when called by
        ProcessMedia in gmg/processing/task.py
        """
        new_size = None

        # Did they specify a size? They must specify either both or none, so
        # we only need to check if one is present
        if reprocess_info.get('max_width'):
            max_width = reprocess_info['max_width']
            max_height = reprocess_info['max_height']

            new_size = (max_width, max_height)

        resize_tool(self.proc_state, False, reprocess_info['resize'],
                    self.name_builder.fill('{basename}.medium{ext}'),
                    self.conversions_subdir, self.exif_tags, new_size)

    def media_reprocess(self, args):
        """
        This function handles the all of the reprocessing logic, before calling
        gmg/submit/lib/run_process_media
        """
        reprocess_args = self._parser(args)
        entry_args = args[0]

        # Can we actually process the given media as requested?
        self._check_eligible(entry_args, reprocess_args)

        # Do we want to re-try initial processing?
        if reprocess_args.initial_processing:
            for id in entry_args.media_id:
                entry = MediaEntry.query.filter_by(id=id).first()
                run_process_media(entry)

        # Are we wanting to resize the thumbnail or medium?
        elif reprocess_args.resize:

            # reprocess all given media entries
            for id in entry_args.media_id:
                entry = MediaEntry.query.filter_by(id=id).first()

                # For now we can only reprocess with the original file
                if not entry.media_files.get('original'):
                    raise Exception(_('The original file for this media entry'
                                      ' does not exist.'))

                reprocess_info = self._get_reprocess_info(reprocess_args)
                run_process_media(entry, reprocess_info=reprocess_info)

        # If we are here, they forgot to tell us how to reprocess
        else:
            _log.warn('You must set either --resize or --initial_processing'
                      ' flag to reprocess an image.')

    def _get_reprocess_info(self, args):
        """ Returns a dict with the info needed for reprocessing"""
        reprocess_info = {'resize': args.resize}

        if args.size:
            reprocess_info['max_width'] = args.size[0]
            reprocess_info['max_height'] = args.size[1]

        return reprocess_info


class CommonImageProcessor(MediaProcessor):
    """
    Provides a base for various media processing steps
    """
    # Common resizing step
    def resize_step(self):
        pass

    @classmethod
    def _add_width_height_args(cls, parser):
        parser.add_argument(
            "--width", default=None,
            help=(
                "Width of the resized image (if not using defaults)"))
        parser.add_argument(
            "--height", default=None,
            help=(
                "Height of the resized image (if not using defaults)"))


class InitialProcessor(CommonImageProcessor):
    """
    Initial processing step for new images
    """
    name = "initial"
    description = "Initial processing"

    @classmethod
    def media_is_eligibile(cls, media_entry):
        """
        Determine if this media type is eligible for processing
        """
        return media_entry.state in (
            "unprocessed", "failed")

    ###############################
    # Command line interface things
    ###############################

    @classmethod
    def generate_parser(cls):
        parser = argparse.ArgumentParser(
            description=cls.description,
            prog=cls.name)

        cls._add_width_height_args(parser)

        return parser

    @classmethod
    def args_to_request(cls, args):
        raise NotImplementedError



class ImageProcessingManager(ProcessingManager):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.add_processor(InitialProcessor)


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
