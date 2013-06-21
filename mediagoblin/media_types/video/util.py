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

from mediagoblin import mg_globals as mgg

_log = logging.getLogger(__name__)


def skip_transcode(metadata):
    '''
    Checks video metadata against configuration values for skip_transcode.

    Returns True if the video matches the requirements in the configuration.
    '''
    config = mgg.global_config['media_type:mediagoblin.media_types.video']\
            ['skip_transcode']

    medium_config = mgg.global_config['media:medium']

    _log.debug('skip_transcode config: {0}'.format(config))

    if config['mime_types'] and metadata.get('mimetype'):
        if not metadata['mimetype'] in config['mime_types']:
            return False

    if config['container_formats'] and metadata['tags'].get('audio-codec'):
        if not metadata['tags']['container-format'] in config['container_formats']:
            return False

    if config['video_codecs'] and metadata['tags'].get('audio-codec'):
        if not metadata['tags']['video-codec'] in config['video_codecs']:
            return False

    if config['audio_codecs'] and metadata['tags'].get('audio-codec'):
        if not metadata['tags']['audio-codec'] in config['audio_codecs']:
            return False

    if config['dimensions_match']:
        if not metadata['videoheight'] <= medium_config['max_height']:
            return False
        if not metadata['videowidth'] <= medium_config['max_width']:
            return False

    return True
