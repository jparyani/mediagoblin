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
import asciitoimage
import chardet
import os
import Image

from mediagoblin import mg_globals as mgg
from mediagoblin.processing import create_pub_filepath, THUMB_SIZE


def process_ascii(entry):
    '''
    Code to process a txt file
    '''
    workbench = mgg.workbench_manager.create_workbench()
    # Conversions subdirectory to avoid collisions
    conversions_subdir = os.path.join(
        workbench.dir, 'conversions')
    os.mkdir(conversions_subdir)

    queued_filepath = entry['queued_media_file']
    queued_filename = workbench.localized_file(
        mgg.queue_store, queued_filepath,
        'source')

    queued_file = file(queued_filename, 'rb')

    with queued_file:
        queued_file_charset = chardet.detect(queued_file.read())

        queued_file.seek(0)  # Rewind the queued file

        thumb_filepath = create_pub_filepath(
            entry, 'thumbnail.png')

        tmp_thumb_filename = os.path.join(
            conversions_subdir, thumb_filepath[-1])

        converter = asciitoimage.AsciiToImage()

        thumb = converter._create_image(
            queued_file.read())

        with file(tmp_thumb_filename, 'w') as thumb_file:
            thumb.thumbnail(THUMB_SIZE, Image.ANTIALIAS)
            thumb.save(thumb_file)

        mgg.public_store.copy_local_to_storage(
            tmp_thumb_filename, thumb_filepath)

        queued_file.seek(0)

        original_filepath = create_pub_filepath(entry, queued_filepath[-1])

        with mgg.public_store.get_file(original_filepath, 'wb') \
            as original_file:
            original_file.write(queued_file.read())


        queued_file.seek(0)  # Rewind *again*

        unicode_filepath = create_pub_filepath(entry, 'unicode.txt')

        with mgg.public_store.get_file(unicode_filepath, 'wb') \
                as unicode_file:
            unicode_file.write(
                    unicode(queued_file.read().decode(
                        queued_file_charset['encoding'])).encode(
                    'ascii',
                    'xmlcharrefreplace'))

    mgg.queue_store.delete_file(queued_filepath)
    entry['queued_media_file'] = []
    media_files_dict = entry.setdefault('media_files', {})
    media_files_dict['thumb'] = thumb_filepath
    media_files_dict['unicode'] = unicode_filepath
    media_files_dict['original'] = original_filepath

    entry.save()
