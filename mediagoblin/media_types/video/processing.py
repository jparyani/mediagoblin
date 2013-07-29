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

from tempfile import NamedTemporaryFile
import logging
import datetime

from mediagoblin import mg_globals as mgg
from mediagoblin.processing import \
    create_pub_filepath, FilenameBuilder, BaseProcessingFail, ProgressCallback
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _

from . import transcoders
from .util import skip_transcode

_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)

MEDIA_TYPE = 'mediagoblin.media_types.video'


class VideoTranscodingFail(BaseProcessingFail):
    '''
    Error raised if video transcoding fails
    '''
    general_message = _(u'Video transcoding failed')


def sniff_handler(media_file, **kw):
    transcoder = transcoders.VideoTranscoder()
    data = transcoder.discover(media_file.name)

    _log.info('Sniffing {0}'.format(MEDIA_TYPE))
    _log.debug('Discovered: {0}'.format(data))

    if not data:
        _log.error('Could not discover {0}'.format(
                kw.get('media')))
        return None

    if data['is_video'] == True:
        return MEDIA_TYPE

    return None


def process_video(proc_state):
    """
    Process a video entry, transcode the queued media files (originals) and
    create a thumbnail for the entry.

    A Workbench() represents a local tempory dir. It is automatically
    cleaned up when this function exits.
    """
    entry = proc_state.entry
    workbench = proc_state.workbench
    video_config = mgg.global_config['media_type:mediagoblin.media_types.video']

    queued_filepath = entry.queued_media_file
    queued_filename = proc_state.get_queued_filename()
    name_builder = FilenameBuilder(queued_filename)

    medium_filepath = create_pub_filepath(
        entry, name_builder.fill('{basename}-640p.webm'))

    thumbnail_filepath = create_pub_filepath(
        entry, name_builder.fill('{basename}.thumbnail.jpg'))

    # Create a temporary file for the video destination (cleaned up with workbench)
    tmp_dst = NamedTemporaryFile(dir=workbench.dir, delete=False)
    with tmp_dst:
        # Transcode queued file to a VP8/vorbis file that fits in a 640x640 square
        progress_callback = ProgressCallback(entry)

        dimensions = (
            mgg.global_config['media:medium']['max_width'],
            mgg.global_config['media:medium']['max_height'])

        # Extract metadata and keep a record of it
        metadata = transcoders.VideoTranscoder().discover(queued_filename)
        store_metadata(entry, metadata)

        # Figure out whether or not we need to transcode this video or
        # if we can skip it
        if skip_transcode(metadata):
            _log.debug('Skipping transcoding')

            dst_dimensions = metadata['videowidth'], metadata['videoheight']

            # Push original file to public storage
            _log.debug('Saving original...')
            proc_state.copy_original(queued_filepath[-1])

            did_transcode = False
        else:
            transcoder = transcoders.VideoTranscoder()

            transcoder.transcode(queued_filename, tmp_dst.name,
                    vp8_quality=video_config['vp8_quality'],
                    vp8_threads=video_config['vp8_threads'],
                    vorbis_quality=video_config['vorbis_quality'],
                    progress_callback=progress_callback,
                    dimensions=dimensions)

            dst_dimensions = transcoder.dst_data.videowidth,\
                    transcoder.dst_data.videoheight

            # Push transcoded video to public storage
            _log.debug('Saving medium...')
            mgg.public_store.copy_local_to_storage(tmp_dst.name, medium_filepath)
            _log.debug('Saved medium')

            entry.media_files['webm_640'] = medium_filepath

            did_transcode = True

        # Save the width and height of the transcoded video
        entry.media_data_init(
            width=dst_dimensions[0],
            height=dst_dimensions[1])

    # Temporary file for the video thumbnail (cleaned up with workbench)
    tmp_thumb = NamedTemporaryFile(dir=workbench.dir, suffix='.jpg', delete=False)

    with tmp_thumb:
        # Create a thumbnail.jpg that fits in a 180x180 square
        transcoders.VideoThumbnailerMarkII(
                queued_filename,
                tmp_thumb.name,
                180)

        # Push the thumbnail to public storage
        _log.debug('Saving thumbnail...')
        mgg.public_store.copy_local_to_storage(tmp_thumb.name, thumbnail_filepath)
        entry.media_files['thumb'] = thumbnail_filepath

    # save the original... but only if we did a transcoding
    # (if we skipped transcoding and just kept the original anyway as the main
    #  media, then why would we save the original twice?)
    if video_config['keep_original'] and did_transcode:
        # Push original file to public storage
        _log.debug('Saving original...')
        proc_state.copy_original(queued_filepath[-1])

    # Remove queued media file from storage and database
    proc_state.delete_queue_file()


def store_metadata(media_entry, metadata):
    """
    Store metadata from this video for this media entry.
    """
    # Let's pull out the easy, not having to be converted ones first
    stored_metadata = dict(
        [(key, metadata[key])
         for key in [
                 "videoheight", "videolength", "videowidth",
                 "audiorate", "audiolength", "audiochannels", "audiowidth",
                 "mimetype"]
         if key in metadata])

    # We have to convert videorate into a sequence because it's a
    # special type normally..

    if "videorate" in metadata:
        videorate = metadata["videorate"]
        stored_metadata["videorate"] = [videorate.num, videorate.denom]

    # Also make a whitelist conversion of the tags.
    if "tags" in metadata:
        tags_metadata = metadata['tags']

        # we don't use *all* of these, but we know these ones are
        # safe...
        tags = dict(
            [(key, tags_metadata[key])
             for key in [
                     "application-name", "artist", "audio-codec", "bitrate",
                     "container-format", "copyright", "encoder",
                     "encoder-version", "license", "nominal-bitrate", "title",
                     "video-codec"]
             if key in tags_metadata])
        if 'date' in tags_metadata:
            date = tags_metadata['date']
            tags['date'] = "%s-%s-%s" % (
                date.year, date.month, date.day)

        # TODO: handle timezone info; gst.get_time_zone_offset +
        #   python's tzinfo should help
        if 'datetime' in tags_metadata:
            dt = tags_metadata['datetime']
            tags['datetime'] = datetime.datetime(
                dt.get_year(), dt.get_month(), dt.get_day(), dt.get_hour(),
                dt.get_minute(), dt.get_second(),
                dt.get_microsecond()).isoformat()

        metadata['tags'] = tags

    # Only save this field if there's something to save
    if len(stored_metadata):
        media_entry.media_data_init(
            orig_metadata=stored_metadata)
