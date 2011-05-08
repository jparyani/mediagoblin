# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 Free Software Foundation, Inc
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

from webob import Response
from mongokit import ObjectId
import wtforms
#from mongokit import ObjectId

def user_home(request):
    """'Homepage' of a User()"""
    user = request.db.User.find_one(
        {'username': request.matchdict['user']})

    medias = request.db.MediaEntry.find()

    template = request.template_env.get_template(
        'mediagoblin/user_pages/user.html')
    return Response(
        template.render(
            {'request': request,
             'user': user,
             'medias': medias}))

def media_home(request):
    """'Homepage' of a MediaEntry()"""
    media = request.db.MediaEntry.find_one(
        ObjectId(request.matchdict['m_id']))

    #check that media uploader and user correspondent
    if media['uploader'].get('username') != request.matchdict['user']:
        #TODO: How do I throw an error 404?
        pass

    template = request.template_env.get_template(
        'mediagoblin/user_pages/media.html')
    return Response(
        template.render(
            {'request': request,
             'media': media}))
