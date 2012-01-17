# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 MediaGoblin contributors.  See AUTHORS.
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
from mediagoblin.tools.template import render_template


def render_to_response(request, template, context, status=200):
    """Much like Django's shortcut.render()"""
    return Response(
        render_template(request, template, context),
        status=status)


def render_404(request):
    """
    Render a 404.
    """
    return render_to_response(
        request, 'mediagoblin/404.html', {}, status=404)


def redirect(request, *args, **kwargs):
    """Returns a HTTPFound(), takes a request and then urlgen params"""

    querystring = None
    if kwargs.get('querystring'):
        querystring = kwargs.get('querystring')
        del kwargs['querystring']

    return exc.HTTPFound(
        location=''.join([
                request.urlgen(*args, **kwargs),
                querystring if querystring else '']))
