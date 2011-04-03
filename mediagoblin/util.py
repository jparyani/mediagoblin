# GNU Mediagoblin -- federated, autonomous media hosting
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

import jinja2
import mongokit

def get_jinja_env(user_template_path=None):
    if user_template_path:
        loader = jinja2.ChoiceLoader(
            [jinja2.FileSystemLoader(user_template_path),
             jinja2.PackageLoader('mediagoblin', 'templates')])
    else:
        loader = jinja2.PackageLoader('mediagoblin', 'templates')

    return jinja2.Environment(loader=loader, autoescape=True)


def setup_user_in_request(request):
    """
    Examine a request and tack on a request.user parameter if that's
    appropriate.
    """
    if not request.session.has_key('user_id'):
        return

    user = None

    try:
        user = request.db.User.one({'_id': request.session['user_id']})
        
        if not user:
            # Something's wrong... this user doesn't exist?  Invalidate
            # this session.
            request.session.invalidate()

    except mongokit.MultipleResultsFound:
        # Something's wrong... we shouldn't have multiple users with
        # the same user id.  Invalidate this session.
        request.session.invalidate()

    request.user = user
