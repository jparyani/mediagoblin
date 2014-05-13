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
import os
from pkg_resources import resource_filename

from mediagoblin.tools.pluginapi import (register_template_path,
                                        register_routes,
                                        register_template_hooks)
from mediagoblin.plugins.archivalook.views import (get_root_view,
                                    add_featured_media_to_media_home)
from mediagoblin.tools.staticdirect import PluginStatic


_log = logging.getLogger(__name__)


_setup_plugin_called = 0

def setup_plugin():
    global _setup_plugin_called

    my_plugin_dir = os.path.dirname(__file__)
    template_dir = os.path.join(my_plugin_dir, 'templates')
    register_template_path(template_dir)
    register_routes([
        ('manage-featured-media', '/mod/feature-media/',
        'mediagoblin.plugins.archivalook.views:featured_media_panel'),
        ('gallery-recent-media', '/recent/',
        'mediagoblin.plugins.archivalook.views:recent_media_gallery_view'),
        ('mediagoblin.user_pages.media_feature',
          '/u/<string:user>/m/<string:media>/feature/',
          'mediagoblin.plugins.archivalook.views:feature_media'),
        ('mediagoblin.user_pages.media_unfeature',
          '/u/<string:user>/m/<string:media>/unfeature/',
          'mediagoblin.plugins.archivalook.views:unfeature_media'),
        ('mediagoblin.user_pages.feature_promote',
          '/u/<string:user>/m/<string:media>/promote_feature/',
          'mediagoblin.plugins.archivalook.views:promote_featured_media'),
        ('mediagoblin.user_pages.feature_demote',
          '/u/<string:user>/m/<string:media>/demote_feature/',
          'mediagoblin.plugins.archivalook.views:demote_featured_media')])
    register_template_hooks({
            'media_sideinfo':'archivalook/feature_media_sidebar.html'})
    register_template_hooks({
            'moderation_powers':'archivalook/bits/feature_dropdown.html'})

    # Add template head hooks, if certain media types are enabled
    from mediagoblin import mg_globals
    plugin_section = mg_globals.global_config.get("plugins", {})
    if "mediagoblin.media_types.video" in plugin_section:
        register_template_hooks({
            "archivalook_feature_head": (
                "/archivalook/feature_displays/video_head.html")})
    if "mediagoblin.media_types.audio" in plugin_section:
        register_template_hooks({
            "archivalook_feature_head": (
                "/archivalook/feature_displays/audio_head.html")})


IMAGE_PRIMARY_TEMPLATE = "/archivalook/feature_displays/image_primary.html"
IMAGE_SECONDARY_TEMPLATE = "/archivalook/feature_displays/image_secondary.html"
IMAGE_TERTIARY_TEMPLATE = "/archivalook/feature_displays/image_tertiary.html"
AUDIO_PRIMARY_TEMPLATE = "/archivalook/feature_displays/audio_primary.html"
AUDIO_SECONDARY_TEMPLATE = "/archivalook/feature_displays/audio_secondary.html"
AUDIO_TERTIARY_TEMPLATE = "/archivalook/feature_displays/audio_tertiary.html"
VIDEO_PRIMARY_TEMPLATE = "/archivalook/feature_displays/video_primary.html"
VIDEO_SECONDARY_TEMPLATE = "/archivalook/feature_displays/video_secondary.html"
VIDEO_TERTIARY_TEMPLATE = "/archivalook/feature_displays/video_tertiary.html"

hooks = {
    'setup': setup_plugin,
    'static_setup': lambda: PluginStatic(
        'archivalook',
        resource_filename('mediagoblin.plugins.archivalook', 'static')
     ),
    'frontpage_view': get_root_view,
    'media_home_context': add_featured_media_to_media_home,

    # # Primary and secondary templates
     ("feature_primary_template",
      "mediagoblin.media_types.image"): lambda: IMAGE_PRIMARY_TEMPLATE,
     ("feature_secondary_template",
      "mediagoblin.media_types.image"): lambda: IMAGE_SECONDARY_TEMPLATE,
     ("feature_primary_template",
      "mediagoblin.media_types.audio"): lambda: AUDIO_PRIMARY_TEMPLATE,
     ("feature_secondary_template",
      "mediagoblin.media_types.audio"): lambda: AUDIO_SECONDARY_TEMPLATE,
    ("feature_primary_template",
     "mediagoblin.media_types.video"): lambda: VIDEO_PRIMARY_TEMPLATE,
     ("feature_secondary_template",
      "mediagoblin.media_types.video"): lambda: VIDEO_SECONDARY_TEMPLATE,
}
