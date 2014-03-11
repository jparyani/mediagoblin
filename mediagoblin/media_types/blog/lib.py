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


def check_blog_slug_used(author_id, slug, ignore_b_id=None):
    from mediagoblin.media_types.blog.models import Blog
    query = Blog.query.filter_by(author=author_id, slug=slug)
    if ignore_b_id:
        query = query.filter(Blog.id != ignore_b_id)
    does_exist = query.first() is not None
    return does_exist
    
def may_edit_blogpost(request, blog):
    if request.user.has_privilege(u'admin') or request.user.id == blog.author:
        return True
    return False

def set_blogpost_state(request, blogpost):
    if request.form['status'] == 'Publish':
        blogpost.state = u'processed'
    else:
        blogpost.state = u'failed'

def get_all_blogposts_of_blog(request, blog, state=None):
    blog_posts_list = []
    blog_post_data = request.db.BlogPostData.query.filter_by(blog=blog.id).all()
    for each_blog_post_data in blog_post_data:
        blog_post = each_blog_post_data.get_media_entry
        if state == None:
            blog_posts_list.append(blog_post)
        if blog_post.state == state:
            blog_posts_list.append(blog_post)
    blog_posts_list.reverse()
    return blog_posts_list

def get_blog_by_slug(request, slug, **kwargs):
    if slug.startswith('blog_'):
        blog_id = int(slug[5:])
        blog = request.db.Blog.query.filter_by(id=blog_id, **kwargs).first()
    else:
        blog = request.db.Blog.query.filter_by(slug=slug, **kwargs).first()
    return blog
 
