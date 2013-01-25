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

import uuid

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


class GenerateSlugMixin(object):
    """
    Mixin to add a generate_slug method to objects.

    Depends on:
     - self.slug
     - self.title
     - self.check_slug_used(new_slug)
    """
    def generate_slug(self):
        """
        Generate a unique slug for this object.

        This one does not *force* slugs, but usually it will probably result
        in a niceish one.

        The end *result* of the algorithm will result in these resolutions for
        these situations:
         - If we have a slug, make sure it's clean and sanitized, and if it's
           unique, we'll use that.
         - If we have a title, slugify it, and if it's unique, we'll use that.
         - If we can't get any sort of thing that looks like it'll be a useful
           slug out of a title or an existing slug, bail, and don't set the
           slug at all.  Don't try to create something just because.  Make
           sure we have a reasonable basis for a slug first.
         - If we have a reasonable basis for a slug (either based on existing
           slug or slugified title) but it's not unique, first try appending
           the entry's id, if that exists
         - If that doesn't result in something unique, tack on some randomly
           generated bits until it's unique.  That'll be a little bit of junk,
           but at least it has the basis of a nice slug.
        """
        #Is already a slug assigned? Check if it is valid
        if self.slug:
            self.slug = slugify(self.slug)

        # otherwise, try to use the title.
        elif self.title:
            # assign slug based on title
            self.slug = slugify(self.title)

        # We don't want any empty string slugs
        if self.slug == u"":
            self.slug = None

        # Do we have anything at this point?
        # If not, we're not going to get a slug
        # so just return... we're not going to force one.
        if not self.slug:
            return  # giving up!

        # Otherwise, let's see if this is unique.
        if self.check_slug_used(self.slug):
            # It looks like it's being used... lame.

            # Can we just append the object's id to the end?
            if self.id:
                slug_with_id = u"%s-%s" % (self.slug, self.id)
                if not self.check_slug_used(slug_with_id):
                    self.slug = slug_with_id
                    return  # success!

            # okay, still no success;
            # let's whack junk on there till it's unique.
            self.slug += '-' + uuid.uuid4().hex[:4]
            # keep going if necessary!
            while self.check_slug_used(self.slug):
                self.slug += uuid.uuid4().hex[:4]


class MediaEntryMixin(GenerateSlugMixin):
    def check_slug_used(self, slug):
        # import this here due to a cyclic import issue
        # (db.models -> db.mixin -> db.util -> db.models)
        from mediagoblin.db.util import check_media_slug_used

        return check_media_slug_used(self.uploader, slug, self.id)

    @property
    def description_html(self):
        """
        Rendered version of the description, run through
        Markdown and cleaned with our cleaning tool.
        """
        return cleaned_markdown_conversion(self.description)

    def get_display_media(self):
        """Find the best media for display.

        We try checking self.media_manager.fetching_order if it exists to
        pull down the order.

        Returns:
          (media_size, media_path)
          or, if not found, None.

        """
        fetch_order = self.media_manager.get("media_fetch_order")

        # No fetching order found?  well, give up!
        if not fetch_order:
            return None

        media_sizes = self.media_files.keys()

        for media_size in fetch_order:
            if media_size in media_sizes:
                return media_size, self.media_files[media_size]

    def main_mediafile(self):
        pass

    @property
    def slug_or_id(self):
        if self.slug:
            return self.slug
        else:
            return u'id:%s' % self.id

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


class CollectionMixin(GenerateSlugMixin):
    def check_slug_used(self, slug):
        # import this here due to a cyclic import issue
        # (db.models -> db.mixin -> db.util -> db.models)
        from mediagoblin.db.util import check_collection_slug_used

        return check_collection_slug_used(self.creator, slug, self.id)

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
