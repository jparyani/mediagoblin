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

from uuid import uuid4

from werkzeug.utils import cached_property

from mediagoblin import mg_globals
from mediagoblin.auth import lib as auth_lib
from mediagoblin.media_types import get_media_managers, FileTypeNotSupported
from mediagoblin.tools import common, licenses
from mediagoblin.tools.text import cleaned_markdown_conversion
from mediagoblin.tools.url import slugify


class UserMixin(object):
    def check_login(self, password):
        """
        See if a user can login with this password
        """
        return auth_lib.bcrypt_check_password(
            password, self.pw_hash)

    @property
    def bio_html(self):
        return cleaned_markdown_conversion(self.bio)


class MediaEntryMixin(object):
    def generate_slug(self):
        # import this here due to a cyclic import issue
        # (db.models -> db.mixin -> db.util -> db.models)
        from mediagoblin.db.util import check_media_slug_used

        #Is already a slug assigned? Check if it is valid
        if self.slug:
            self.slug = slugify(self.slug)
        elif self.title:
            #assign slug based on title
            self.slug = slugify(self.title)
        elif self.id:
            # Does the object already have an ID? (after adding to the session)
            self.slug = unicode(self.id)
        else:
            # Everything else failed, just use random garbage
            self.slug = unicode(uuid4())[1:4]

        while check_media_slug_used(self.uploader, self.slug, self.id):
            # add garbage till it's unique
            self.slug = self.slug + unicode(uuid4())[1:4]

    @property
    def description_html(self):
        """
        Rendered version of the description, run through
        Markdown and cleaned with our cleaning tool.
        """
        return cleaned_markdown_conversion(self.description)

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

    @property
    def slug_or_id(self):
        return (self.slug or self.id)


    def url_for_self(self, urlgen, **extra_args):
        """
        Generate an appropriate url for ourselves

        Use a slug if we have one, else use our 'id'.
        """
        uploader = self.get_uploader

        return urlgen(
            'mediagoblin.user_pages.media_home',
            user=uploader.username,
            media=self.slug_or_id,
            **extra_args)

    @property
    def thumb_url(self):
        """Return the thumbnail URL (for usage in templates)
        Will return either the real thumbnail or a default fallback icon."""
        # TODO: implement generic fallback in case MEDIA_MANAGER does
        # not specify one?
        if u'thumb' in self.media_files:
            thumb_url = mg_globals.app.public_store.file_url(
                            self.media_files[u'thumb'])
        else:
            # No thumbnail in media available. Get the media's
            # MEDIA_MANAGER for the fallback icon and return static URL
            # Raises FileTypeNotSupported in case no such manager is enabled
            manager = self.media_manager
            thumb_url = mg_globals.app.staticdirector(manager[u'default_thumb'])
        return thumb_url

    @cached_property
    def media_manager(self):
        """Returns the MEDIA_MANAGER of the media's media_type

        Raises FileTypeNotSupported in case no such manager is enabled
        """
        # TODO, we should be able to make this a simple lookup rather
        # than iterating through all media managers.
        for media_type, manager in get_media_managers():
            if media_type == self.media_type:
                return manager
        # Not found?  Then raise an error
        raise FileTypeNotSupported(
            "MediaManager not in enabled types.  Check media_types in config?")

    def get_fail_exception(self):
        """
        Get the exception that's appropriate for this error
        """
        if self.fail_error:
            return common.import_component(self.fail_error)

    def get_license_data(self):
        """Return license dict for requested license"""
        return licenses.get_license_by_url(self.license or "")

    def exif_display_iter(self):
        from mediagoblin.tools.exif import USEFUL_TAGS

        if not self.media_data:
            return
        exif_all = self.media_data.get("exif_all")

        for key in USEFUL_TAGS:
            if key in exif_all:
                yield key, exif_all[key]


class MediaCommentMixin(object):
    @property
    def content_html(self):
        """
        the actual html-rendered version of the comment displayed.
        Run through Markdown and the HTML cleaner.
        """
        return cleaned_markdown_conversion(self.content)


class CollectionMixin(object):
    def generate_slug(self):
        # import this here due to a cyclic import issue
        # (db.models -> db.mixin -> db.util -> db.models)
        from mediagoblin.db.util import check_collection_slug_used

        self.slug = slugify(self.title)

        duplicate = check_collection_slug_used(mg_globals.database,
            self.creator, self.slug, self.id)

        if duplicate:
            if self.id is not None:
                self.slug = u"%s-%s" % (self.id, self.slug)
            else:
                self.slug = None

    @property
    def description_html(self):
        """
        Rendered version of the description, run through
        Markdown and cleaned with our cleaning tool.
        """
        return cleaned_markdown_conversion(self.description)

    @property
    def slug_or_id(self):
        return (self.slug or self.id)

    def url_for_self(self, urlgen, **extra_args):
        """
        Generate an appropriate url for ourselves

        Use a slug if we have one, else use our 'id'.
        """
        creator = self.get_creator

        return urlgen(
            'mediagoblin.user_pages.user_collection',
            user=creator.username,
            collection=self.slug_or_id,
            **extra_args)


class CollectionItemMixin(object):
    @property
    def note_html(self):
        """
        the actual html-rendered version of the note displayed.
        Run through Markdown and the HTML cleaner.
        """
        return cleaned_markdown_conversion(self.note)
