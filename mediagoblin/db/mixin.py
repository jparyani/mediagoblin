# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011,2012 MediaGoblin contributors.  See AUTHORS.
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

"""
This module contains some Mixin classes for the db objects.

A bunch of functions on the db objects are really more like
"utility functions": They could live outside the classes
and be called "by hand" passing the appropiate reference.
They usually only use the public API of the object and
rarely use database related stuff.

These functions now live here and get "mixed in" into the
real objects.
"""

from mediagoblin.auth import lib as auth_lib
from mediagoblin.tools import common


class UserMixin(object):
    def check_login(self, password):
        """
        See if a user can login with this password
        """
        return auth_lib.bcrypt_check_password(
            password, self.pw_hash)


class MediaEntryMixin(object):
    def get_display_media(self, media_map,
                          fetch_order=common.DISPLAY_IMAGE_FETCHING_ORDER):
        """
        Find the best media for display.

        Args:
        - media_map: a dict like
          {u'image_size': [u'dir1', u'dir2', u'image.jpg']}
        - fetch_order: the order we should try fetching images in

        Returns:
        (media_size, media_path)
        """
        media_sizes = media_map.keys()

        for media_size in common.DISPLAY_IMAGE_FETCHING_ORDER:
            if media_size in media_sizes:
                return media_map[media_size]

    def main_mediafile(self):
        pass

    def url_for_self(self, urlgen):
        """
        Generate an appropriate url for ourselves

        Use a slug if we have one, else use our '_id'.
        """
        uploader = self.get_uploader

        if self.get('slug'):
            return urlgen(
                'mediagoblin.user_pages.media_home',
                user=uploader.username,
                media=self.slug)
        else:
            return urlgen(
                'mediagoblin.user_pages.media_home',
                user=uploader.username,
                media=unicode(self._id))

    def get_fail_exception(self):
        """
        Get the exception that's appropriate for this error
        """
        if self['fail_error']:
            return common.import_component(self['fail_error'])
