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

import logging
import tempfile
import os

from mediagoblin import mg_globals as mgg
from mediagoblin.processing import create_pub_filepath

from mediagoblin.media_types.audio.transcoders import AudioTranscoder

_log = logging.getLogger()

def sniff_handler(media):
    return True

def process_audio(entry):
    audio_config = mgg.global_config['media_type:mediagoblin.media_types.audio']

    workbench = mgg.workbench_manager.create_workbench()

    queued_filepath = entry.queued_media_file
    queued_filename = workbench.localized_file(
        mgg.queue_store, queued_filepath,
        'source')

    ogg_filepath = create_pub_filepath(
        entry,
        '{original}.webm'.format(
            original=os.path.splitext(
                queued_filepath[-1])[0]))

    ogg_tmp = tempfile.NamedTemporaryFile()

    with ogg_tmp:
        transcoder = AudioTranscoder()

        transcoder.transcode(
            queued_filename,
            ogg_tmp.name,
            quality=audio_config['quality'])

        data = transcoder.discover(ogg_tmp.name)

        _log.debug('Saving medium...')
        mgg.public_store.get_file(ogg_filepath, 'wb').write(
            ogg_tmp.read())

        entry.media_files['ogg'] = ogg_filepath

        entry.media_data['audio'] = {
            u'length': int(data.audiolength)}

    thumbnail_tmp = tempfile.NamedTemporaryFile()

    with thumbnail_tmp:
        entry.media_files['thumb'] = ['fake', 'thumb', 'path.jpg']

    mgg.queue_store.delete_file(queued_filepath)

    entry.save()
