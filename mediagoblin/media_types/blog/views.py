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
from mediagoblin.media_types.blog.models import Blog, BlogPostData
from mediagoblin.media_types.blog.lib import may_edit_blogpost

from mediagoblin.messages import add_message, SUCCESS, ERROR
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

from mediagoblin.notifications import add_comment_subscription


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
            if request.method == 'POST' and form.validate():
                blog.title = unicode(form.title.data)
                blog.description = unicode(form.description.data)
                blog.author = request.user.id
                blog.generate_slug()
                
                blog.save()
                add_message(request, SUCCESS, "Your blog is updated.")
                return redirect(request, "mediagoblin.user_pages.user_home",
                            user=request.user.username)            
            
@require_active_login        
def blogpost_create(request):
    

    form = blog_forms.BlogPostEditForm(request.form, license=request.user.license_preference)
     
    if request.method == 'POST' and form.validate():
        blog_slug = request.matchdict.get('blog_slug')
        blog = request.db.Blog.query.filter_by(slug=blog_slug,
            author=request.user.id).first()
        

        blogpost = request.db.MediaEntry()
        blogpost.media_type = 'mediagoblin.media_types.blogpost'
        blogpost.title = unicode(form.title.data)
        blogpost.description = unicode(form.description.data)
        blogpost.tags =  convert_to_tag_list_of_dicts(form.tags.data)
        blogpost.license = unicode(form.license.data) or None
        blogpost.uploader = request.user.id
        blogpost.state = 'processed'
        
        blogpost.generate_slug()
        
        blogpost.save()
        
        # connect this blogpost to its blog
        blog_post_data = request.db.BlogPostData()
        blog_post_data.blog = blog.id
        blog_post_data.media_entry = blogpost.id
        blog_post_data.save()
    
        add_message(request, SUCCESS, _('Woohoo! Submitted!'))
        add_comment_subscription(request.user, blogpost)
        return redirect(request, "mediagoblin.user_pages.user_home", 
            user=request.user.username)
        
    return render_to_response(
        request,
        'mediagoblin/blog/blog_post_edit_create.html',
        {'form': form,
        'app_config': mg_globals.app_config,
        'user': request.user.username})


@require_active_login
def blogpost_edit(request):
    blog_slug = request.matchdict.get('blog_slug')
    blog_post_slug = request.matchdict.get('blog_post_slug')

    blog = request.db.Blog.query.filter_by(slug=blog_slug, author=request.user.id).first()
    blog_post_data = request.db.BlogPostData.query.filter_by(blog=blog.id).first()

    blogpost = blog_post_data.get_media_entry

    defaults = dict(
                title = blogpost.title,
                description = blogpost.description,
                tags=media_tags_as_string(blogpost.tags),
                license=blogpost.license)
    
    form = blog_forms.BlogPostEditForm(request.form, **defaults)
    if request.method == 'POST' and form.validate():
        blogpost.title = unicode(form.title.data)
        blogpost.description = unicode(form.description.data)
        blogpost.tags =  convert_to_tag_list_of_dicts(form.tags.data)
        blogpost.license = unicode(form.license.data) 
        
        blogpost.generate_slug()
        blogpost.save()
        
        add_message(request, SUCCESS, _('Woohoo! edited blogpost is submitted'))
        return redirect(request, "mediagoblin.user_pages.user_home", 
            user=request.user.username)
    
    return render_to_response(
        request,
        'mediagoblin/blog/blog_post_edit_create.html',
        {'form': form,
        'app_config': mg_globals.app_config,
        'user': request.user.username,
        'blog_post_slug': blog_post_slug
        })    

@require_active_login
def blog_dashboard(request):
    blog_posts_list = []
    blog_slug = request.matchdict.get('blog_slug')
    _log.info(blog_slug)

    blog = request.db.Blog.query.filter_by(slug=blog_slug).first()
    blog_post_data = request.db.BlogPostData.query.filter_by(blog=blog.id).all()

    for each_blog_post_data in blog_post_data:
        blog_post = each_blog_post_data.get_media_entry
        if blog_post:
            blog_posts_list.append(blog_post)
    blog_post_count = len(blog_posts_list)

    if may_edit_blogpost(request, blog):
        return render_to_response(
        request,
        'mediagoblin/blog/blog_admin_dashboard.html',
        {'blog_posts_list': blog_posts_list,
        'blog_slug':blog_slug,
        'blog':blog,
        'blog_post_count':blog_post_count
        })

                                                            
    
    
    
 
