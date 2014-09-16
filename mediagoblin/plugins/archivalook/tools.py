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
from mediagoblin.db.models import MediaEntry, User
from mediagoblin.plugins.archivalook.models import FeaturedMedia
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _
from mediagoblin.plugins.archivalook.models import FeaturedMedia

def get_media_entry_from_uploader_slug(uploader_username, slug):
    """
    Accepts two strings and searches to see if those strings identify a
    MediaEntry

    :param uploader_username            A string representing the User.username
                                        of the user who uploaded a piece of
                                        media.
    :param slug                         A string representing the slug of a
                                        piece of media

    :returns media                      A MediaEntry object or None if no entry
                                        matches the specifications.
    """
    uploader = User.query.filter(
                User.username == uploader_username).first()
    media = MediaEntry.query.filter(
                MediaEntry.get_uploader == uploader ).filter(
                MediaEntry.slug == slug).first()
    return media


def parse_url(url):
    """
    A simple helper function that extracts the uploader and slug from a full url

    :param url                          A string containing the url for a piece
                                        of media. This should be in the format
                                        of "/u/{user}/m/{media}/"

    :returns (uploader_username, slug)  Uploader_username is a unicode string
                                        representing the username of the user
                                        who uploaded the piece of media, slug is
                                        the media entry's url slug.
    """
    url = unicode(url)
    u_end, m_start, m_end, end = (url.find('/u/') + 3,
                                  url.find('/m/'),
                                  url.find('/m/') + 3,
                                  url.rfind('/'))

    uploader_username = url[u_end:m_start].strip()
    slug = url[m_end:end].strip()

    return uploader_username, slug


def split_featured_media_list(featured_media):
    """
    This script is part of processing post request on the /mod/feature-media/
    page. Post requests on these pages will only include the textbox, so this
    script accepts the textbox's contents as its parameter.

    :parameter  featured_media                  A string from a submitted
                                                textarea within the post request
                                                on /mod/feature-media/

    :returns    all_featured_media              A dictionary of the format
                                                MediaEntry : 'string'
                                                where MediaEntry is a featured
                                                piece of media and 'string' is
                                                a string representation of its
                                                display type (primary, secondary
                                                or tertiary)
    """

    featured_media = unicode(featured_media)
    featured_media_list = featured_media.split("\n")
    display_type = 0
    media_already_featured = []
    all_featured_media = []
    for line in featured_media_list:
        if line == '' or line.isspace(): continue
        elif line.startswith(u'-'):
            display_type += 1
        elif display_type <= 0 or display_type > 3: continue
        else:
            uploader, slug = parse_url(line)
            media = get_media_entry_from_uploader_slug(uploader, slug)
            # Make sure the media entry referenced exists, and has not already
            # been featured higher up the list
            if media == None or media in media_already_featured: continue
            media_already_featured.append(media)
            all_featured_media.append((media,
                [None,
                u'primary',
                u'secondary',
                u'tertiary'][display_type]))

    return all_featured_media


def create_featured_media_textbox():
    """
    This script searches through the database of which media is featured and
    returns a string of each entry in the proper format for use in the
    /mod/feature-media/ page. This string will be used as the default text in
    the textbox on that page.
    """

    primaries = FeaturedMedia.query.order_by(
        FeaturedMedia.order.asc()).filter(
        FeaturedMedia.display_type == u'primary').all()
    secondaries = FeaturedMedia.query.order_by(
        FeaturedMedia.order.asc()).filter(
        FeaturedMedia.display_type == u'secondary').all()
    tertiaries = FeaturedMedia.query.order_by(
        FeaturedMedia.order.asc()).filter(
        FeaturedMedia.display_type == u'tertiary').all()
    output_text = u''
    for display_type, feature_list in [
            (_(u'Primary'),primaries),
            (_(u'Secondary'),secondaries),
            (_(u'Tertiary'),tertiaries)]:
        output_text += _(
            u"""-----------{display_type}-Features---------------------------
""").format(display_type=display_type)
        for feature in feature_list:
            media_entry = feature.media_entry
            output_text += u'/u/{uploader_username}/m/{media_slug}/\n'.format(
                uploader_username = media_entry.get_uploader.username,
                media_slug = media_entry.slug)


    return output_text

def automatically_add_new_feature(media_entry):
    """
    This function automates the addition of a new feature. New features will be
    placed at the top of the feature stack as 'primary' features. All of the
    current features are demoted one step to make room.

    :param media_entry :type mediagoblin.db.MediaEntry
                                                The media entry that will been
                                                featured which this function
                                                targets
    """
    # Set variables to determine which media entries should be pushed down to
    # maintain the correct number of primary & secondary featured media. At this
    # point the program assumes that there should be 1 primary feature and 2
    # secondary features, but in the future this should be a variable editable
    # by the site admin.
    too_many_primaries = FeaturedMedia.query.filter(
        FeaturedMedia.display_type==u'primary').count() >= 1
    too_many_secondaries = FeaturedMedia.query.filter(
        FeaturedMedia.display_type==u'secondary').count() >= 2
    featured_first_to_last = FeaturedMedia.query.order_by(
        FeaturedMedia.order.asc()).all()

    for feature in featured_first_to_last:
        # Some features have the option to demote or promote themselves to a
        # different display_type, based on their position. But all features move
        # up and down one step in the stack.
        if (feature.is_last_of_type() and feature.display_type == u'primary'
                and too_many_primaries):
            feature.demote()
            too_many_primaries = False
        elif (feature.is_last_of_type() and feature.display_type == u'secondary'
                and too_many_secondaries):
            feature.demote()
            too_many_secondaries = False
        feature.move_down()
        feature.save()

    # Create the new feature at the top of the stack.
    new_feature = FeaturedMedia(
        media_entry=media_entry,
        display_type=u"primary",
        order=0)
    new_feature.save()
    return new_feature

def automatically_remove_feature(media_entry):
    """
    This function automates the removal of a feature. All of the features below
    them are promoted one step to close the gap.

    :param media_entry :type mediagoblin.db.MediaEntry
                                                The media entry that will been
                                                removed which this function
                                                targets
    """
    # Get the feature which will be deleted
    target_feature = FeaturedMedia.query.filter(
        FeaturedMedia.media_entry_id == media_entry.id).first()
    # Find out which continuing features will have to be adjusted
    featured_last_to_first = FeaturedMedia.query.filter(
        FeaturedMedia.order>target_feature.order).order_by(
        FeaturedMedia.order.desc()).all()

    for feature in featured_last_to_first:
        # Maintain the current arrangement of primary/secondary/tertiary
        # features by moving all the features below the deleted one up on slot
        # and promoting any features in the proper position.
        if feature.is_first_of_type():
            feature.promote()
        feature.move_up()
        feature.save()

    # Delete the feature, now that it's space has been closed
    target_feature.delete()

def promote_feature(media_entry):
    """
    This function takes a current feature and moves it up the stack so that it
    will be displayed higher up. It swaps the place of the selected feature for
    the one above it, or if relevant raises the display_type of the feature up
    one rung (ie. from 'tertiary' to 'secondary')

    :param media_entry :type mediagoblin.db.MediaEntry
                                                The media entry that has been
                                                featured which this function
                                                targets
    """
    # Get the FeaturedMedia object
    target_feature = FeaturedMedia.query.filter(
        FeaturedMedia.media_entry_id == media_entry.id).first()
    # Get the first Feature with a lower order than the target
    above_feature = FeaturedMedia.query.filter(
        FeaturedMedia.order < target_feature.order).order_by(
        FeaturedMedia.order.desc()).first()
    # If the feature is not the uppermost one
    if above_feature is not None:
        # Swap the positions of the target feature with the one before it
        (target_feature.order,
         above_feature.order) = above_feature.order, target_feature.order
        (target_feature.display_type,
         above_feature.display_type) = (above_feature.display_type,
                                        target_feature.display_type)
        above_feature.save()
    # Change the feature's display type to a more prominent one
    elif target_feature.display_type == u'secondary':
        target_feature.display_type = u'primary'
    elif target_feature.display_type == u'tertiary':
        target_feature.display_type = u'secondary'
    target_feature.save()

def demote_feature(media_entry):
    """
    This function takes a current feature and moves it down the stack so that it
    will be displayed lower down. It swaps the place of the selected feature for
    the one below it, or if relevant lowers the display_type of the feature down
    one rung (ie. from 'secondary' to 'tertiary')

    :param media_entry :type mediagoblin.db.MediaEntry
                                                The media entry that has been
                                                featured which this function
                                                targets
    """
    # Get the FeaturedMedia object
    target_feature = FeaturedMedia.query.filter(
        FeaturedMedia.media_entry_id == media_entry.id).first()
    # Get the first Feature with a higher order than the target
    below_feature = FeaturedMedia.query.filter(
        FeaturedMedia.order > target_feature.order).order_by(
        FeaturedMedia.order.asc()).first()
    # If the feature is not the lowest one
    if below_feature != None:
        # Swap the positions of the target feature with the one after it
        (target_feature.order,
         below_feature.order) = below_feature.order, target_feature.order
        (target_feature.display_type,
         below_feature.display_type) = (below_feature.display_type,
                                        target_feature.display_type)
        below_feature.save()
    # Change the feature's display type to a less prominent one
    elif target_feature.display_type == u'secondary':
        target_feature.display_type = u'tertiary'
    elif target_feature.display_type == u'primary':
        target_feature.display_type = u'secondary'
    target_feature.save()

