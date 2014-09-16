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
from mediagoblin import mg_globals
from mediagoblin.db.base import Session
from mediagoblin.db.models import MediaEntry
from mediagoblin.decorators import uses_pagination, user_not_banned,\
                                  user_has_privilege, get_user_media_entry
from mediagoblin.tools.response import render_to_response, redirect
from mediagoblin.tools.pagination import Pagination

from mediagoblin.plugins.archivalook.tools import (
                                        split_featured_media_list,
                                        create_featured_media_textbox,
                                        automatically_add_new_feature,
                                        automatically_remove_feature)
from mediagoblin.plugins.archivalook import forms as archivalook_forms
from mediagoblin.plugins.archivalook.models import FeaturedMedia
from mediagoblin.plugins.archivalook.utils import feature_template
from mediagoblin.plugins.archivalook.tools import (promote_feature,
                                                    demote_feature)
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _

@user_not_banned
def root_view(request):
    """
    This is an alternative to the typical root view. This display centers around
    displaying featured media.
    """
    featured_media = {
        u'primary':FeaturedMedia.query.order_by(
            FeaturedMedia.order.asc()).filter(
            FeaturedMedia.display_type==u'primary').all(),
        u'secondary':FeaturedMedia.query.order_by(
            FeaturedMedia.order.asc()).filter(
            FeaturedMedia.display_type==u'secondary').all(),
        u'tertiary':FeaturedMedia.query.order_by(
            FeaturedMedia.order.asc()).filter(
            FeaturedMedia.display_type==u'tertiary').all()}

    return render_to_response(
        request, 'archivalook/root.html',
       {'featured_media': featured_media,
        'allow_registration': mg_globals.app_config["allow_registration"],
        'feature_template': feature_template})

@user_has_privilege(u'featurer')
def featured_media_panel(request):
    """
    This is a new administrator panel to manage featured media. This is an
    entirely optional panel, as there are other ways to manage it, but this way
    gives the admin more control.
    """
    form = archivalook_forms.FeaturedMediaList(request.form)

    if request.method == 'POST' and form.validate():
        featured_media = split_featured_media_list(form.box_content.data)
        previous_features = FeaturedMedia.query.all()
        for index, (media_entry, display_type) in enumerate(featured_media):
            target = FeaturedMedia.query.filter(
                FeaturedMedia.media_entry == media_entry).first()
            # If this media was already featured, we don't have to create a new
            # feature, we just have to edit the old one's values
            if target is not None:
                target.order = index
                target.display_type = display_type
                previous_features.remove(target)
                Session.add(target)
            else:
                new_feature = FeaturedMedia(
                    media_entry=media_entry,
                    display_type=display_type,
                    order=index)
                Session.add(new_feature)
        [Session.delete(feature) for feature in previous_features]

        Session.commit()

    form.box_content.data = create_featured_media_textbox()
    return render_to_response(
        request, 'archivalook/feature.html',
       {'form' : form})

@uses_pagination
@user_not_banned
def recent_media_gallery_view(request, page):
    """
    The replaced homepage is available through this view.
    """
    cursor = MediaEntry.query.filter_by(state=u'processed').\
        order_by(MediaEntry.created.desc())

    pagination = Pagination(page, cursor)
    media_entries = pagination()
    return render_to_response(
        request, 'archivalook/recent_media.html',
        {'media_entries': media_entries,
         'pagination': pagination})

def add_featured_media_to_media_home(context):
    """
    A context hook which allows the media home page to know whether the media
    has been featured or not.
    """
    context['featured_media'] = FeaturedMedia.query
    return context

@user_has_privilege(u'featurer')
@get_user_media_entry
def feature_media(request, media, **kwargs):
    """
    A view to feature a new piece of media
    """
    already_featured_media_ids = [f.media_entry.id 
        for f in FeaturedMedia.query.all()]
    if not media.id in already_featured_media_ids:
        new_feature = automatically_add_new_feature(media)
    return redirect(
        request, 'index')

@user_has_privilege(u'featurer')
@get_user_media_entry
def unfeature_media(request, media, **kwargs):
    """
    A view to unfeature a piece of media which has previously been featured.
    """
    already_featured_media_ids = [f.media_entry.id 
        for f in FeaturedMedia.query.all()]
    if media.id in already_featured_media_ids:
        automatically_remove_feature(media)
    return redirect(
        request, 'index')

@user_has_privilege(u'featurer')
@get_user_media_entry
def promote_featured_media(request, media, **kwargs):
    """
    A view to move a piece of media up the featured stack
    """
    featured_media = FeaturedMedia.query.filter(
        FeaturedMedia.media_entry_id == media.id).first()
    if featured_media is not None:
        promote_feature(media)
    return redirect(
        request, 'index')

@user_has_privilege(u'featurer')
@get_user_media_entry
def demote_featured_media(request, media, **kwargs):
    """
    A view to move a piece of media down the featured stack
    """
    featured_media = FeaturedMedia.query.filter(
        FeaturedMedia.media_entry_id == media.id).first()
    if featured_media is not None:
        demote_feature(media)
    return redirect(
        request, 'index')

def get_root_view():
    return root_view
