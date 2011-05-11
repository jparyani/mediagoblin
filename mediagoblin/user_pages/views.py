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

from webob import Response, exc
from mongokit import ObjectId
import wtforms


def user_home(request):
    """'Homepage' of a User()"""
    user = request.db.User.find_one({
            'username': request.matchdict['user'],
            'status': 'active'})
    if not user:
        return exc.HTTPNotFound()

    medias = request.db.MediaEntry.find({
            'uploader': user,
            'state': 'processed'})

    template = request.template_env.get_template(
        'mediagoblin/user_pages/user.html')
    return Response(
        template.render(
            {'request': request,
             'user': user,
             'media_entries': medias}))


def media_home(request):
    """'Homepage' of a MediaEntry()"""
    media = request.db.MediaEntry.find_one({
            '_id': ObjectId(request.matchdict['m_id']),
            'state': 'processed'})

    # Check that media uploader and user correspond.
    if not media or \
            media['uploader'].get('username') != request.matchdict['user']:
        return exc.HTTPNotFound()

    template = request.template_env.get_template(
        'mediagoblin/user_pages/media.html')
    return Response(
        template.render(
            {'request': request,
             'media': media}))
