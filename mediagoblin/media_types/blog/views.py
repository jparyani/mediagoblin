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

from datetime import datetime

from werkzeug.exceptions import Forbidden

from mediagoblin import messages
from mediagoblin import mg_globals

from mediagoblin.media_types.blog import forms as blog_forms
#from mediagoblin.edit.lib import may_edit_media
from mediagoblin.decorators import (require_active_login, active_user_from_url,
                            get_media_entry_by_id, user_may_alter_collection,
                            get_user_collection)
from mediagoblin.tools.response import (render_to_response,
                                        redirect, redirect_obj, render_404)
from mediagoblin.tools.translate import pass_to_ugettext as _
from mediagoblin.tools.template import render_template
from mediagoblin.tools.text import (
    convert_to_tag_list_of_dicts, media_tags_as_string)
from mediagoblin.tools.url import slugify
from mediagoblin.db.util import check_media_slug_used, check_collection_slug_used
from mediagoblin.db.models import User, Collection

@require_active_login
def blog_create(request, media=None):
    """
    View to create and edit a blog
    """
    
    blog_form = blog_forms.BlogEditForm(request.form) 

    if request.method == 'POST' and blog_form.validate():
        blog = request.db.Collection()

        blog.title = unicode(blog_form.title.data)
        blog.description = unicode(blog_form.description.data)
        blog.creator = request.user.id
        blog.generate_slug()

        # Make sure this user isn't duplicating an existing collection
        existing_blog_name = request.db.Collection.find_one({
                'creator': request.user.id,
                'title':blog.title})

        if existing_blog_name:
            add_message(request, messages.ERROR,
                _('You already have a blog called "%s"!') \
                    % blog.title)
        else:
            blog.save()

            add_message(request, SUCCESS,
                _('Blog "%s" added!') % blog.title)

        return redirect(request, "mediagoblin.user_pages.user_home",
                        user=request.user.username)

    return render_to_response(
        request,
        'mediagoblin/blog/blog_edit_create.html',
        {'blog_form': blog_form,
         'app_config': mg_globals.app_config})

@require_active_login  
@user_may_alter_collection
@get_user_collection 
def blog_edit(request, collection):
    """
    View for editing an existing blog which is a collection of MediaEntries.
    """
    blog = collection
    defaults = dict(
		title = blog.title,
		description = blog.description)
    existing_blog = request.db.Collection.find_one({
				'creator': request.user.id,
                'title':blog_form.title.data})
    if existing_blog and existing_blog.id != blog.id: 
		messages.add_message(
			request, messages.ERROR,
			_('You already have a blog called "%s"!') % \
                    blog_form.title.data)
    else:
            blog.title = unicode(blog_form.title.data)
            blog.description = unicode(blog_form.description.data)
            
	    blog.save()

            return redirect_obj(request, blog)

    if request.user.is_admin \
            and blog.creator != request.user.id \
            and request.method != 'POST':
        messages.add_message(
            request, messages.WARNING,
            _("You are editing another user's blog. Proceed with caution."))

    return render_to_response(
        request,
        'mediagoblin/blog/blog_edit_create.html',
        {'blog': blog,
         'form': blog_form})
			
			
			
			
			
			
			
			
		

	
