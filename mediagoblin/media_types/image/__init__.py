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
import argparse
import datetime
import logging

from mediagoblin.db.models import MediaEntry
from mediagoblin.media_types import MediaManagerBase
from mediagoblin.media_types.image.processing import process_image, \
    sniff_handler
from mediagoblin.submit.lib import run_process_media
from mediagoblin.tools import pluginapi
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _

_log = logging.getLogger(__name__)


ACCEPTED_EXTENSIONS = ["jpg", "jpeg", "png", "gif", "tiff"]
MEDIA_TYPE = 'mediagoblin.media_types.image'


def setup_plugin():
    config = pluginapi.get_config('mediagoblin.media_types.image')


class ImageMediaManager(MediaManagerBase):
    human_readable = "Image"
    processor = staticmethod(process_image)
    display_template = "mediagoblin/media_displays/image.html"
    default_thumb = "images/media_thumbs/image.png"

    media_fetch_order = [u'medium', u'original', u'thumb']

    def get_original_date(self):
        """
        Get the original date and time from the EXIF information. Returns
        either a datetime object or None (if anything goes wrong)
        """
        if not self.entry.media_data or not self.entry.media_data.exif_all:
            return None

        try:
            # Try wrapped around all since exif_all might be none,
            # EXIF DateTimeOriginal or printable might not exist
            # or strptime might not be able to parse date correctly
            exif_date = self.entry.media_data.exif_all[
                'EXIF DateTimeOriginal']['printable']
            original_date = datetime.datetime.strptime(
                exif_date,
                '%Y:%m:%d %H:%M:%S')
            return original_date
        except (KeyError, ValueError):
            return None


def get_media_type_and_manager(ext):
    if ext in ACCEPTED_EXTENSIONS:
        return MEDIA_TYPE, ImageMediaManager


def reprocess_action(args):
    if args[0].state == 'processed':
        print _('\n Available reprocessing actions for processed images:'
                '\n \t --resize: thumb or medium'
                '\n Options:'
                '\n \t --size: max_width max_height (defaults to config specs)')
        return True


def _parser(args):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--resize')
    parser.add_argument(
        '--size',
        nargs=2,
        type=int)
    parser.add_argument(
        '--initial_processing',
        action='store_true')

    return parser.parse_args(args[1])


def _check_eligible(entry_args, reprocess_args):
    if entry_args.state == 'processed':
        if reprocess_args.initial_processing:
            raise Exception(_('You can not run --initial_processing on media'
                              ' that has already been processed.'))

    if entry_args.state == 'failed':
        if reprocess_args.resize:
            raise Exception(_('You can not run --resize on media that has not'
                              ' been processed.'))
        if reprocess_args.size:
            _log.warn('With --initial_processing, the --size flag will be'
                      ' ignored.')

    if entry_args.state == 'processing':
        raise Exception(_('We currently do not support reprocessing on media'
                          ' that is in the "processing" state.'))


def media_reprocess(args):
    reprocess_args = _parser(args)
    entry_args = args[0]

    _check_eligible(entry_args, reprocess_args)
    if reprocess_args.initial_processing:
        for id in entry_args.media_id:
            entry = MediaEntry.query.filter_by(id=id).first()
            # Should we get the feed_url?
            run_process_media(entry)

    elif reprocess_args.resize:
        if reprocess_args.resize == 'medium' or reprocess_args.resize == \
           'thumb':
            for id in entry_args.media_id:
                entry = MediaEntry.query.filter_by(id=id).first()

                # For now we can only reprocess with the original file
                if not entry.media_files.get('original'):
                    raise Exception(_('The original file for this media entry'
                                      ' does not exist.'))

                reprocess_info = {'resize': reprocess_args.resize}

                if reprocess_args.size:
                    reprocess_info['max_width'] = reprocess_args.size[0]
                    reprocess_info['max_height'] = reprocess_args.size[1]

                run_process_media(entry, reprocess_info=reprocess_info)

        else:
            raise Exception(_('The --resize flag must set either "thumb"'
                              ' or "medium".'))

    else:
        _log.warn('You must set either --resize or --initial_processing flag'
                  ' to reprocess an image.')


hooks = {
    'setup': setup_plugin,
    'get_media_type_and_manager': get_media_type_and_manager,
    'sniff_handler': sniff_handler,
    ('media_manager', MEDIA_TYPE): lambda: ImageMediaManager,
    ('reprocess_action', 'image'): reprocess_action,
    ('media_reprocess', 'image'): media_reprocess,
}
