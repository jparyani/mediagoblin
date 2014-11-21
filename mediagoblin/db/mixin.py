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
import re
from datetime import datetime

from pytz import UTC
from werkzeug.utils import cached_property

from mediagoblin import mg_globals
from mediagoblin.media_types import FileTypeNotSupported
from mediagoblin.tools import common, licenses
from mediagoblin.tools.pluginapi import hook_handle
from mediagoblin.tools.text import cleaned_markdown_conversion
from mediagoblin.tools.url import slugify
from mediagoblin.tools.translate import pass_to_ugettext as _


class UserMixin(object):
    object_type = "person"

    @property
    def bio_html(self):
        return cleaned_markdown_conversion(self.bio)

    def url_for_self(self, urlgen, **kwargs):
        """Generate a URL for this User's home page."""
        return urlgen('mediagoblin.user_pages.user_home',
                      user=self.username, **kwargs)


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
            slug = slugify(self.slug)

        # otherwise, try to use the title.
        elif self.title:
            # assign slug based on title
            slug = slugify(self.title)

        else:
            # We don't have any information to set a slug
            return

        # We don't want any empty string slugs
        if slug == u"":
            return

        # Otherwise, let's see if this is unique.
        if self.check_slug_used(slug):
            # It looks like it's being used... lame.

            # Can we just append the object's id to the end?
            if self.id:
                slug_with_id = u"%s-%s" % (slug, self.id)
                if not self.check_slug_used(slug_with_id):
                    self.slug = slug_with_id
                    return  # success!

            # okay, still no success;
            # let's whack junk on there till it's unique.
            slug += '-' + uuid.uuid4().hex[:4]
            # keep going if necessary!
            while self.check_slug_used(slug):
                slug += uuid.uuid4().hex[:4]

        # self.check_slug_used(slug) must be False now so we have a slug that
        # we can use now.
        self.slug = slug


class MediaEntryMixin(GenerateSlugMixin):
    def check_slug_used(self, slug):
        # import this here due to a cyclic import issue
        # (db.models -> db.mixin -> db.util -> db.models)
        from mediagoblin.db.util import check_media_slug_used

        return check_media_slug_used(self.uploader, slug, self.id)

    @property
    def object_type(self):
        """ Converts media_type to pump-like type - don't use internally """
        return self.media_type.split(".")[-1]

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
        fetch_order = self.media_manager.media_fetch_order

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

    @property
    def original_url(self):
        """ Returns the URL for the original image
        will return self.thumb_url if original url doesn't exist"""
        if u"original" not in self.media_files:
            return self.thumb_url

        return mg_globals.app.public_store.file_url(
            self.media_files[u"original"]
            )

    @cached_property
    def media_manager(self):
        """Returns the MEDIA_MANAGER of the media's media_type

        Raises FileTypeNotSupported in case no such manager is enabled
        """
        manager = hook_handle(('media_manager', self.media_type))
        if manager:
            return manager(self)

        # Not found?  Then raise an error
        raise FileTypeNotSupported(
            "MediaManager not in enabled types. Check media_type plugins are"
            " enabled in config?")

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
        if not self.media_data:
            return
        exif_all = self.media_data.get("exif_all")

        for key in exif_all:
            label = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', key)
            yield label.replace('EXIF', '').replace('Image', ''), exif_all[key]

    def exif_display_data_short(self):
        """Display a very short practical version of exif info"""
        if not self.media_data:
            return

        exif_all = self.media_data.get("exif_all")

        exif_short = {}

        if 'Image DateTimeOriginal' in exif_all:
            # format date taken
            takendate = datetime.strptime(
                exif_all['Image DateTimeOriginal']['printable'],
                '%Y:%m:%d %H:%M:%S').date()
            taken = takendate.strftime('%B %d %Y')

            exif_short.update({'Date Taken': taken})

        aperture = None
        if 'EXIF FNumber' in exif_all:
            fnum = str(exif_all['EXIF FNumber']['printable']).split('/')

            # calculate aperture
            if len(fnum) == 2:
                aperture = "f/%.1f" % (float(fnum[0])/float(fnum[1]))
            elif fnum[0] != 'None':
                aperture = "f/%s" % (fnum[0])

        if aperture:
            exif_short.update({'Aperture': aperture})

        short_keys = [
            ('Camera', 'Image Model', None),
            ('Exposure', 'EXIF ExposureTime', lambda x: '%s sec' % x),
            ('ISO Speed', 'EXIF ISOSpeedRatings', None),
            ('Focal Length', 'EXIF FocalLength', lambda x: '%s mm' % x)]

        for label, key, fmt_func in short_keys:
            try:
                val = fmt_func(exif_all[key]['printable']) if fmt_func \
                        else exif_all[key]['printable']
                exif_short.update({label: val})
            except KeyError:
                pass

        return exif_short


class MediaCommentMixin(object):
    object_type = "comment"

    @property
    def content_html(self):
        """
        the actual html-rendered version of the comment displayed.
        Run through Markdown and the HTML cleaner.
        """
        return cleaned_markdown_conversion(self.content)

    def __unicode__(self):
        return u'<{klass} #{id} {author} "{comment}">'.format(
            klass=self.__class__.__name__,
            id=self.id,
            author=self.get_author,
            comment=self.content)

    def __repr__(self):
        return '<{klass} #{id} {author} "{comment}">'.format(
            klass=self.__class__.__name__,
            id=self.id,
            author=self.get_author,
            comment=self.content)


class CollectionMixin(GenerateSlugMixin):
    object_type = "collection"

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

class ActivityMixin(object):
    object_type = "activity"

    VALID_VERBS = ["add", "author", "create", "delete", "dislike", "favorite",
                   "follow", "like", "post", "share", "unfavorite", "unfollow",
                   "unlike", "unshare", "update", "tag"]

    def get_url(self, request):
        return request.urlgen(
            "mediagoblin.federation.activity_view",
            username=self.get_actor.username,
            id=self.id,
            qualified=True
        )

    def generate_content(self):
        """ Produces a HTML content for object """
        # some of these have simple and targetted. If self.target it set
        # it will pick the targetted. If they DON'T have a targetted version
        # the information in targetted won't be added to the content.
        verb_to_content = {
            "add": {
                "simple" : _("{username} added {object}"),
                "targetted":  _("{username} added {object} to {target}"),
            },
            "author": {"simple": _("{username} authored {object}")},
            "create": {"simple": _("{username} created {object}")},
            "delete": {"simple": _("{username} deleted {object}")},
            "dislike": {"simple": _("{username} disliked {object}")},
            "favorite": {"simple": _("{username} favorited {object}")},
            "follow": {"simple": _("{username} followed {object}")},
            "like": {"simple": _("{username} liked {object}")},
            "post": {
                "simple": _("{username} posted {object}"),
                "targetted": _("{username} posted {object} to {target}"),
            },
            "share": {"simple": _("{username} shared {object}")},
            "unfavorite": {"simple": _("{username} unfavorited {object}")},
            "unfollow": {"simple": _("{username} stopped following {object}")},
            "unlike": {"simple": _("{username} unliked {object}")},
            "unshare": {"simple": _("{username} unshared {object}")},
            "update": {"simple": _("{username} updated {object}")},
            "tag": {"simple": _("{username} tagged {object}")},
        }

        obj = self.get_object
        target = self.get_target
        actor = self.get_actor
        content = verb_to_content.get(self.verb, None)

        if content is None or obj is None:
            return

        if target is None or "targetted" not in content:
            self.content = content["simple"].format(
                username=actor.username,
                object=obj.object_type
            )
        else:
            self.content = content["targetted"].format(
                username=actor.username,
                object=obj.object_type,
                target=target.object_type,
            )

        return self.content

    def serialize(self, request):
        href = request.urlgen(
            "mediagoblin.federation.object",
            object_type=self.object_type,
            id=self.id,
            qualified=True
        )
        published = UTC.localize(self.published)
        updated = UTC.localize(self.updated)
        obj = {
            "id": href,
            "actor": self.get_actor.serialize(request),
            "verb": self.verb,
            "published": published.isoformat(),
            "updated": updated.isoformat(),
            "content": self.content,
            "url": self.get_url(request),
            "object": self.get_object.serialize(request),
            "objectType": self.object_type,
        }

        if self.generator:
            obj["generator"] = self.get_generator.serialize(request)

        if self.title:
            obj["title"] = self.title

        target = self.get_target
        if target is not None:
            obj["target"] = target.serialize(request)

        return obj

    def unseralize(self, data):
        """
        Takes data given and set it on this activity.

        Several pieces of data are not written on because of security
        reasons. For example changing the author or id of an activity.
        """
        if "verb" in data:
            self.verb = data["verb"]

        if "title" in data:
            self.title = data["title"]

        if "content" in data:
            self.content = data["content"]
