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

_log = logging.getLogger(__name__)

from datetime import datetime

from werkzeug.exceptions import Forbidden

from mediagoblin import mg_globals

from mediagoblin.media_types.blog import forms as blog_forms
from mediagoblin.media_types.blog.models import Blog
from mediagoblin.messages import add_message, SUCCESS, ERROR
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
from mediagoblin.db.models import User, Collection, MediaEntry


@require_active_login
def blog_edit(request):
    """
    View for editing the existing blog or automatically
    creating a new blog if user does not have any yet.
    """
    url_user = request.matchdict.get('user', None)
    blog_slug = request.matchdict.get('blog_slug', None)
    
    max_blog_count = 1
    form = blog_forms.BlogEditForm(request.form)
    # the blog doesn't exists yet
    if not blog_slug:
        if Blog.query.filter_by(author=request.user.id).count()<max_blog_count:
            if request.method=='GET':
                return render_to_response(
                    request,
                    'mediagoblin/blog/blog_edit_create.html',
                    {'form': form,
                    'user' : request.user,
                    'app_config': mg_globals.app_config})

            if request.method=='POST' and form.validate():
                _log.info("Here")
                blog = Blog()
                blog.title = unicode(form.title.data)
                blog.description = unicode(form.description.data)  #remember clean html data.
                blog.author = request.user.id
                blog.generate_slug()
               
                blog.save()
                return redirect(request, "mediagoblin.user_pages.user_home",
                        user=request.user.username)
        else:
            add_message(request, ERROR, "You can not create any more blogs")
            return redirect(request, "mediagoblin.user_pages.user_home",
                        user=request.user.username)



    else:
        if request.method == 'GET':
            blog = Blog.query.filter_by(slug=blog_slug).first()
            defaults = dict(
                title = blog.title,
                description = blog.description,
                author = request.user.id) 
            
            form = blog_forms.BlogEditForm(**defaults)

            return render_to_response(
                    request,
                    'mediagoblin/blog/blog_edit_create.html',
                    {'form': form,
                     'user': request.user,
                     'app_config': mg_globals.app_config})
        else:
            pass            
        
        
            
            
    
