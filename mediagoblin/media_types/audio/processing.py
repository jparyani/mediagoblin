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
from tempfile import NamedTemporaryFile
import os

from mediagoblin import mg_globals as mgg
from mediagoblin.processing import (create_pub_filepath, BadMediaFail,
    FilenameBuilder, ProgressCallback)

from mediagoblin.media_types.audio.transcoders import (AudioTranscoder,
    AudioThumbnailer)

_log = logging.getLogger(__name__)

MEDIA_TYPE = 'mediagoblin.media_types.audio'


def sniff_handler(media_file, **kw):
    _log.info('Sniffing {0}'.format(MEDIA_TYPE))
    try:
        transcoder = AudioTranscoder()
        data = transcoder.discover(media_file.name)
    except BadMediaFail:
        _log.debug('Audio discovery raised BadMediaFail')
        return None

    if data.is_audio == True and data.is_video == False:
        return MEDIA_TYPE

    return None


def process_audio(proc_state):
    """Code to process uploaded audio. Will be run by celery.

    A Workbench() represents a local tempory dir. It is automatically
    cleaned up when this function exits.
    """
    entry = proc_state.entry
    workbench = proc_state.workbench
    audio_config = mgg.global_config['media_type:mediagoblin.media_types.audio']

    queued_filepath = entry.queued_media_file
    queued_filename = workbench.localized_file(
        mgg.queue_store, queued_filepath,
        'source')
    name_builder = FilenameBuilder(queued_filename)

    webm_audio_filepath = create_pub_filepath(
        entry,
        '{original}.webm'.format(
            original=os.path.splitext(
                queued_filepath[-1])[0]))

    if audio_config['keep_original']:
        with open(queued_filename, 'rb') as queued_file:
            original_filepath = create_pub_filepath(
                entry, name_builder.fill('{basename}{ext}'))

            with mgg.public_store.get_file(original_filepath, 'wb') as \
                    original_file:
                _log.debug('Saving original...')
                original_file.write(queued_file.read())

            entry.media_files['original'] = original_filepath

    transcoder = AudioTranscoder()

    with NamedTemporaryFile(dir=workbench.dir) as webm_audio_tmp:
        progress_callback = ProgressCallback(entry)

        transcoder.transcode(
            queued_filename,
            webm_audio_tmp.name,
            quality=audio_config['quality'],
            progress_callback=progress_callback)

        transcoder.discover(webm_audio_tmp.name)

        _log.debug('Saving medium...')
        mgg.public_store.get_file(webm_audio_filepath, 'wb').write(
            webm_audio_tmp.read())

        entry.media_files['webm_audio'] = webm_audio_filepath

        # entry.media_data_init(length=int(data.audiolength))

    if audio_config['create_spectrogram']:
        spectrogram_filepath = create_pub_filepath(
            entry,
            '{original}-spectrogram.jpg'.format(
                original=os.path.splitext(
                    queued_filepath[-1])[0]))

        with NamedTemporaryFile(dir=workbench.dir, suffix='.ogg') as wav_tmp:
            _log.info('Creating OGG source for spectrogram')
            transcoder.transcode(
                queued_filename,
                wav_tmp.name,
                mux_string='vorbisenc quality={0} ! oggmux'.format(
                    audio_config['quality']))

            thumbnailer = AudioThumbnailer()

            with NamedTemporaryFile(dir=workbench.dir, suffix='.jpg') as spectrogram_tmp:
                thumbnailer.spectrogram(
                    wav_tmp.name,
                    spectrogram_tmp.name,
                    width=mgg.global_config['media:medium']['max_width'],
                    fft_size=audio_config['spectrogram_fft_size'])

                _log.debug('Saving spectrogram...')
                mgg.public_store.get_file(spectrogram_filepath, 'wb').write(
                    spectrogram_tmp.read())

                entry.media_files['spectrogram'] = spectrogram_filepath

                with NamedTemporaryFile(dir=workbench.dir, suffix='.jpg') as thumb_tmp:
                    thumbnailer.thumbnail_spectrogram(
                        spectrogram_tmp.name,
                        thumb_tmp.name,
                        (mgg.global_config['media:thumb']['max_width'],
                         mgg.global_config['media:thumb']['max_height']))

                    thumb_filepath = create_pub_filepath(
                        entry,
                        '{original}-thumbnail.jpg'.format(
                            original=os.path.splitext(
                                queued_filepath[-1])[0]))

                    mgg.public_store.get_file(thumb_filepath, 'wb').write(
                        thumb_tmp.read())

                    entry.media_files['thumb'] = thumb_filepath
    else:
        entry.media_files['thumb'] = ['fake', 'thumb', 'path.jpg']

    # Remove queued media file from storage and database.
    # queued_filepath is in the task_id directory which should
    # be removed too, but fail if the directory is not empty to be on
    # the super-safe side.
    mgg.queue_store.delete_file(queued_filepath)      # rm file
    mgg.queue_store.delete_dir(queued_filepath[:-1])  # rm dir
    entry.queued_media_file = []
