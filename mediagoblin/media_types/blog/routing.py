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

from mediagoblin.tools.routing import add_route

#URL mapping for blog-admin, where all the blog posts of a particular blog
#are listed. providing the facility of edit, delete and view a particular blog post."
add_route('mediagoblin.media_types.blog.blog-dashboard', \
	'/u/<string:user>/b/<string:blog_slug>/blog_dashboard/', 'mediagoblin.media_types.blog.views:blog_dashboard')

#URL mapping for creating a new blog post. (add blo_slug in the url at "blogpost" place later"
add_route('mediagoblin.media_types.blog.blogpost.create',
          '/u/<string:user>/b/<string:blog_slug>/p/create/',
	      'mediagoblin.media_types.blog.views:blogpost_create')

#URL mapping for editing an existing blog post.
add_route('mediagoblin.media_types.blog.blogpost.edit', 
          '/u/<string:user>/b/<string:blog_slug>/p/<string:blog_post_slug>/edit/',
	      'mediagoblin.media_types.blog.views:blogpost_edit')

#URL mapping for blog-collection-admin, where all the blogs of the user
#are listed. providing the facility of edit, delete and view a blog. 
#view facility redirects to blog-admin page of that particular blog.  
add_route('mediagoblin.media_types.blog.blog-collection-admin', \
	'/u/<string:user>/blog-collection-admin/', 'mediagoblin.media_types.blog.views:blog-collection-admin')

#URL mapping for creating a new blog.
add_route('mediagoblin.media_types.blog.create', '/u/<string:user>/b/create/',
	'mediagoblin.media_types.blog.views:blog_edit')


#URL mapping for editing an existing blog.
add_route('mediagoblin.media_types.blog.edit', '/u/<string:user>/b/<string:blog_slug>/edit/',
	'mediagoblin.media_types.blog.views:blog_edit')
	
#URL mapping for blog_post_listing view.
add_route('mediagoblin.media_types.blog.blog_post_listing', '/u/<string:user>/b/',
	'mediagoblin.media_types.blog.views:blog_post_listing')
	




	
