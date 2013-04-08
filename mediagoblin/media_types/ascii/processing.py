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
import chardet
import os
import Image
import logging

from mediagoblin import mg_globals as mgg
from mediagoblin.processing import create_pub_filepath
from mediagoblin.media_types.ascii import asciitoimage

_log = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = ['txt', 'asc', 'nfo']


def sniff_handler(media_file, **kw):
    if kw.get('media') is not None:
        name, ext = os.path.splitext(kw['media'].filename)
        clean_ext = ext[1:].lower()

        if clean_ext in SUPPORTED_EXTENSIONS:
            return True

    return False


def process_ascii(proc_state):
    """Code to process a txt file. Will be run by celery.

    A Workbench() represents a local tempory dir. It is automatically
    cleaned up when this function exits. 
    """
    entry = proc_state.entry
    workbench = proc_state.workbench
    ascii_config = mgg.global_config['media_type:mediagoblin.media_types.ascii']
    # Conversions subdirectory to avoid collisions
    conversions_subdir = os.path.join(
        workbench.dir, 'conversions')
    os.mkdir(conversions_subdir)

    queued_filepath = entry.queued_media_file
    queued_filename = workbench.localized_file(
        mgg.queue_store, queued_filepath,
        'source')

    queued_file = file(queued_filename, 'rb')

    with queued_file:
        queued_file_charset = chardet.detect(queued_file.read())

        # Only select a non-utf-8 charset if chardet is *really* sure
        # Tested with "Feli\x0109an superjaron", which was detecte
        if queued_file_charset['confidence'] < 0.9:
            interpreted_charset = 'utf-8'
        else:
            interpreted_charset = queued_file_charset['encoding']

        _log.info('Charset detected: {0}\nWill interpret as: {1}'.format(
                queued_file_charset,
                interpreted_charset))

        queued_file.seek(0)  # Rewind the queued file

        thumb_filepath = create_pub_filepath(
            entry, 'thumbnail.png')

        tmp_thumb_filename = os.path.join(
            conversions_subdir, thumb_filepath[-1])

        ascii_converter_args = {}

        if ascii_config['thumbnail_font']:
            ascii_converter_args.update(
                    {'font': ascii_config['thumbnail_font']})

        converter = asciitoimage.AsciiToImage(
               **ascii_converter_args)

        thumb = converter._create_image(
            queued_file.read())

        with file(tmp_thumb_filename, 'w') as thumb_file:
            thumb.thumbnail(
                (mgg.global_config['media:thumb']['max_width'],
                 mgg.global_config['media:thumb']['max_height']),
                Image.ANTIALIAS)
            thumb.save(thumb_file)

        _log.debug('Copying local file to public storage')
        mgg.public_store.copy_local_to_storage(
            tmp_thumb_filename, thumb_filepath)

        queued_file.seek(0)

        original_filepath = create_pub_filepath(entry, queued_filepath[-1])

        with mgg.public_store.get_file(original_filepath, 'wb') \
            as original_file:
            original_file.write(queued_file.read())

        queued_file.seek(0)  # Rewind *again*

        unicode_filepath = create_pub_filepath(entry, 'ascii-portable.txt')

        with mgg.public_store.get_file(unicode_filepath, 'wb') \
                as unicode_file:
            # Decode the original file from its detected charset (or UTF8)
            # Encode the unicode instance to ASCII and replace any non-ASCII
            # with an HTML entity (&#
            unicode_file.write(
                unicode(queued_file.read().decode(
                        interpreted_charset)).encode(
                    'ascii',
                    'xmlcharrefreplace'))

    # Remove queued media file from storage and database.
    # queued_filepath is in the task_id directory which should
    # be removed too, but fail if the directory is not empty to be on
    # the super-safe side.
    mgg.queue_store.delete_file(queued_filepath)      # rm file
    mgg.queue_store.delete_dir(queued_filepath[:-1])  # rm dir
    entry.queued_media_file = []

    media_files_dict = entry.setdefault('media_files', {})
    media_files_dict['thumb'] = thumb_filepath
    media_files_dict['unicode'] = unicode_filepath
    media_files_dict['original'] = original_filepath

    entry.save()
