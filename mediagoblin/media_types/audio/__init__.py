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

from mediagoblin.media_types import MediaManagerBase
from mediagoblin.media_types.audio.processing import process_audio, \
    sniff_handler
from mediagoblin.tools import pluginapi

# Why isn't .ogg in this list?  It's still detected, but via sniffing,
# .ogg files could be either video or audio... sniffing determines which.

ACCEPTED_EXTENSIONS = ["mp3", "flac", "wav", "m4a"]
MEDIA_TYPE = 'mediagoblin.media_types.audio'


def setup_plugin():
    config = pluginapi.get_config(MEDIA_TYPE)


class AudioMediaManager(MediaManagerBase):
    human_readable = "Audio"
    processor = staticmethod(process_audio)
    display_template = "mediagoblin/media_displays/audio.html"


def get_media_type_and_manager(ext):
    if ext in ACCEPTED_EXTENSIONS:
        return MEDIA_TYPE, AudioMediaManager

hooks = {
    'setup': setup_plugin,
    'get_media_type_and_manager': get_media_type_and_manager,
    'sniff_handler': sniff_handler,
    ('media_manager', MEDIA_TYPE): lambda: AudioMediaManager,
}
