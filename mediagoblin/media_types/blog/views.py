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
from mediagoblin.tools import pluginapi

from mediagoblin import mg_globals

from mediagoblin.media_types.blog import forms as blog_forms
from mediagoblin.media_types.blog.models import Blog, BlogPostData
from mediagoblin.media_types.blog.lib import may_edit_blogpost, set_blogpost_state, get_all_blogposts_of_blog

from mediagoblin.messages import add_message, SUCCESS, ERROR
from mediagoblin.decorators import (require_active_login, active_user_from_url,
                            get_media_entry_by_id, user_may_alter_collection,
                            get_user_collection, uses_pagination)
from mediagoblin.tools.pagination import Pagination
from mediagoblin.tools.response import (render_to_response,
                                        redirect, render_404)
from mediagoblin.tools.translate import pass_to_ugettext as _
from mediagoblin.tools.template import render_template
from mediagoblin.tools.text import (
    convert_to_tag_list_of_dicts, media_tags_as_string, clean_html,
    cleaned_markdown_conversion)

from mediagoblin.db.util import check_media_slug_used, check_collection_slug_used
from mediagoblin.db.models import User, Collection, MediaEntry

from mediagoblin.notifications import add_comment_subscription


@require_active_login
def blog_edit(request):
    """
    View for editing an existing blog or creating a new blog 
    if user have not exceeded maximum allowed acount of blogs.
    """
    url_user = request.matchdict.get('user', None)
    blog_slug = request.matchdict.get('blog_slug', None)

    config = pluginapi.get_config('mediagoblin.media_types.blog')
    max_blog_count = config['max_blog_count']
    form = blog_forms.BlogEditForm(request.form)
    # creating a blog
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
                blog = request.db.Blog()
                blog.title = unicode(form.title.data)
                blog.description = unicode(cleaned_markdown_conversion((form.description.data)))
                blog.author = request.user.id
                blog.generate_slug()

                blog.save()
                return redirect(request, "mediagoblin.media_types.blog.blog_admin_dashboard",
                        user=request.user.username
                       )
        else:
            add_message(request, ERROR, "Welcome! You already have created \
                                                        maximum number of blogs.")
            return redirect(request, "mediagoblin.media_types.blog.blog_admin_dashboard",
                        user=request.user.username)


    #Blog already exists.
    else:
        blog = request.db.Blog.query.filter_by(slug=blog_slug).first()
        if not blog:
            return render_404(request)
        if request.method == 'GET':
            defaults = dict(
                title = blog.title,
                description = cleaned_markdown_conversion(blog.description),
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
                blog.description = unicode(cleaned_markdown_conversion((form.description.data)))
                blog.author = request.user.id
                blog.generate_slug()

                blog.save()
                add_message(request, SUCCESS, "Your blog is updated.")
                return redirect(request, "mediagoblin.media_types.blog.blog-dashboard",
                        user=request.user.username,
                        blog_slug=blog.slug)


@require_active_login
def blogpost_create(request):

    form = blog_forms.BlogPostEditForm(request.form, license=request.user.license_preference)

    if request.method == 'POST' and form.validate():
        blog_slug = request.matchdict.get('blog_slug')
        blog = request.db.Blog.query.filter_by(slug=blog_slug,
            author=request.user.id).first()
        if not blog:
            return render_404(request)

        blogpost = request.db.MediaEntry()
        blogpost.media_type = 'mediagoblin.media_types.blogpost'
        blogpost.title = unicode(form.title.data)
        blogpost.description = unicode(cleaned_markdown_conversion((form.description.data)))
        blogpost.tags =  convert_to_tag_list_of_dicts(form.tags.data)
        blogpost.license = unicode(form.license.data) or None
        blogpost.uploader = request.user.id
        blogpost.generate_slug()

        set_blogpost_state(request, blogpost)
        blogpost.save()

        # connect this blogpost to its blog
        blog_post_data = request.db.BlogPostData()
        blog_post_data.blog = blog.id
        blog_post_data.media_entry = blogpost.id
        blog_post_data.save()

        add_message(request, SUCCESS, _('Woohoo! Submitted!'))
        add_comment_subscription(request.user, blogpost)
        return redirect(request, "mediagoblin.media_types.blog.blog-dashboard",
                        user=request.user.username,
                        blog_slug=blog.slug)

    return render_to_response(
        request,
        'mediagoblin/blog/blog_post_edit_create.html',
        {'form': form,
        'app_config': mg_globals.app_config,
        'user': request.user.username})


@require_active_login
def blogpost_edit(request):
    
    blog_slug = request.matchdict.get('blog_slug', None)
    blog_post_slug = request.matchdict.get('blog_post_slug', None)

    blogpost = request.db.MediaEntry.query.filter_by(slug=blog_post_slug, uploader=request.user.id).first()
    blog = request.db.Blog.query.filter_by(slug=blog_slug, author=request.user.id).first()

    if not blogpost or not blog:
        return render_404(request)

    defaults = dict(
                title = blogpost.title,
                description = cleaned_markdown_conversion(blogpost.description),
                tags=media_tags_as_string(blogpost.tags),
                license=blogpost.license)

    form = blog_forms.BlogPostEditForm(request.form, **defaults)
    if request.method == 'POST' and form.validate():
        blogpost.title = unicode(form.title.data)
        blogpost.description = unicode(cleaned_markdown_conversion((form.description.data)))
        blogpost.tags =  convert_to_tag_list_of_dicts(form.tags.data)
        blogpost.license = unicode(form.license.data)
        set_blogpost_state(request, blogpost)
        blogpost.generate_slug()
        blogpost.save()

        add_message(request, SUCCESS, _('Woohoo! edited blogpost is submitted'))
        return redirect(request, "mediagoblin.media_types.blog.blog-dashboard",
                        user=request.user.username,
                        blog_slug=blog.slug)

    return render_to_response(
        request,
        'mediagoblin/blog/blog_post_edit_create.html',
        {'form': form,
        'app_config': mg_globals.app_config,
        'user': request.user.username,
        'blog_post_slug': blog_post_slug
        })


@active_user_from_url
@uses_pagination
def blog_dashboard(request, page, url_user=None):
    """
    Dashboard for a blog, only accessible to
    the owner of the blog.
    """
    blog_slug = request.matchdict.get('blog_slug', None)
    blogs = request.db.Blog.query.filter_by(author=url_user.id)
    config = pluginapi.get_config('mediagoblin.media_types.blog')
    max_blog_count = config['max_blog_count']
    if request.user and (request.user.id == url_user.id or request.user.has_privilege(u'admin')):
        if blog_slug:
            blog = blogs.filter(Blog.slug==blog_slug).first()
            if not blog:
                return render_404(request)
            else:
                blog_posts_list = blog.get_all_blog_posts().order_by(MediaEntry.created.desc())
                pagination = Pagination(page, blog_posts_list)
                pagination.per_page = 15
                blog_posts_on_a_page = pagination()
                if may_edit_blogpost(request, blog):
                    return render_to_response(
                        request,
                        'mediagoblin/blog/blog_admin_dashboard.html',
                        {'blog_posts_list': blog_posts_on_a_page,
                        'blog_slug':blog_slug,
                        'blog':blog,
                        'user':url_user,
                        'pagination':pagination
                        })
    if not request.user or request.user.id != url_user.id or not blog_slug:
        blogs = blogs.all()
        return render_to_response(
        request,
        'mediagoblin/blog/list_of_blogs.html',
        {
        'blogs':blogs,
        'user':url_user,
        'max_blog_count':max_blog_count
        })


@active_user_from_url
@uses_pagination
def blog_post_listing(request, page, url_user=None):
    """
    Page, listing all the blog posts of a particular blog.
    """
    blog_slug = request.matchdict.get('blog_slug', None)
    blog = request.db.Blog.query.filter_by(slug=blog_slug).first()
    if not blog:
        return render_404(request)

    all_blog_posts = blog.get_all_blog_posts(u'processed').order_by(MediaEntry.created.desc())
    pagination = Pagination(page, all_blog_posts)
    pagination.per_page = 8
    blog_posts_on_a_page = pagination()

    return render_to_response(
        request,
        'mediagoblin/blog/blog_post_listing.html',
        {'blog_posts': blog_posts_on_a_page,
         'pagination': pagination,
         'blog_owner': url_user,
         'blog':blog
        })
        

@require_active_login
def draft_view(request):
    
    blog_slug = request.matchdict.get('blog_slug', None)
    blog_post_slug = request.matchdict.get('blog_post_slug', None)
    user = request.matchdict.get('user')

    blog = request.db.Blog.query.filter_by(author=request.user.id, slug=blog_slug).first()
    blogpost = request.db.MediaEntry.query.filter_by(state = u'failed', uploader=request.user.id, slug=blog_post_slug).first()

    if not blog or not blogpost:
        return render_404(request)

    return render_to_response(
        request,
        'mediagoblin/blog/blogpost_draft_view.html',
        {'blogpost':blogpost,
         'blog': blog
         })
  
         
@require_active_login
def blog_delete(request, **kwargs):
    """
    Deletes a blog and media entries, tags associated with it. 
    """
    url_user = request.matchdict.get('user')
    owner_user = request.db.User.query.filter_by(username=url_user).first()

    blog_slug = request.matchdict.get('blog_slug', None)
    blog = request.db.Blog.query.filter_by(slug=blog_slug, author=owner_user.id).first()
    if not blog:
        return render_404(reequest)

    form = blog_forms.ConfirmDeleteForm(request.form)
    if request.user.id == blog.author or request.user.has_privilege(u'admin'):
        if request.method == 'POST' and form.validate():
            if form.confirm.data is True:
                blog.delete()
                add_message(
                request, SUCCESS, _('You deleted the Blog.'))
                return redirect(request, "mediagoblin.media_types.blog.blog_admin_dashboard",
                        user=request.user.username)
            else:
                add_message(
                request, ERROR,
                _("The media was not deleted because you didn't check that you were sure."))
                return redirect(request, "mediagoblin.media_types.blog.blog_admin_dashboard",
                        user=request.user.username)
        else:
            if request.user.has_privilege(u'admin'):
                add_message(
                    request, WARNING,
                    _("You are about to delete another user's Blog. "
                      "Proceed with caution."))
            return render_to_response(
            request,
            'mediagoblin/blog/blog_confirm_delete.html',
            {'blog':blog,
            'form':form
            })
    else:
        add_message(
        request, ERROR,
        _("The blog was not deleted because you have no rights."))
        return redirect(request, "mediagoblin.media_types.blog.blog_admin_dashboard",
        user=request.user.username)
        
        
def blog_about_view(request):
    """
    Page containing blog description and statistics
    """
    blog_slug = request.matchdict.get('blog_slug', None)
    url_user = request.matchdict.get('user', None)
    
    user = request.db.User.query.filter_by(username=url_user).first() 
    blog = request.db.Blog.query.filter_by(author=user.id, slug=blog_slug).first()
    
    if not user or not blog:
        return render_404(request)
    
    else:
        blog_posts_processed = blog.get_all_blog_posts(u'processed').count()
        return render_to_response(
                request,
                'mediagoblin/blog/blog_about.html',
                {'user': user,
                'blog': blog,
                'blogpost_count': blog_posts_processed
                })
        
    
    





