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

from webob import Response, exc
from mediagoblin.tools.template import render_template
from mediagoblin.tools.translate import fake_ugettext_passthrough as _


def render_to_response(request, template, context, status=200):
    """Much like Django's shortcut.render()"""
    return Response(
        render_template(request, template, context),
        status=status)


def render_error(request, status=500, title=_('Oops!'),
                 err_msg=_('An error occured')):
    """Render any error page with a given error code, title and text body

    Title and description are passed through as-is to allow html. Make
    sure no user input is contained therein for security reasons. The
    description will be wrapped in <p></p> tags.
    """
    return Response(render_template(request, 'mediagoblin/error.html',
        {'err_code': status, 'title': title, 'err_msg': err_msg}),
        status=status)


def render_403(request):
    """Render a standard 403 page"""
    title = _('Operation not allowed')
    err_msg = _("Sorry Dave, I can't let you do that!</p><p>You have tried "
                " to perform a function that you are not allowed to. Have you "
                "been trying to delete all user accounts again?")
    return render_error(request, 403, title, err_msg)

def render_404(request):
    """Render a standard 404 page."""
    err_msg = _("There doesn't seem to be a page at this address. Sorry!</p>"
                "<p>If you're sure the address is correct, maybe the page "
                "you're looking for has been moved or deleted.")
    return render_error(request, 404, err_msg=err_msg)

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
