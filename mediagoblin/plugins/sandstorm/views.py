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
from mediagoblin import mg_globals, messages
from mediagoblin.auth.tools import register_user, create_basic_user
from mediagoblin.db.models import User, Privilege
from mediagoblin.decorators import allow_registration, auth_enabled
from mediagoblin.tools.translate import pass_to_ugettext as _
from mediagoblin.tools.response import redirect, render_to_response
from mediagoblin.plugins.sandstorm.models import SandstormUser

from random import getrandbits
import urllib


@auth_enabled
def login(request):
    login_failed = False

    username = request.headers.get('X-Sandstorm-Username', None)
    user_id = request.headers.get('X-Sandstorm-User-Id', None)
    permissions = request.headers.get('X-Sandstorm-Permissions', None)

    if username != None:
        username = urllib.unquote(username)
    if permissions != None:
        permissions = urllib.unquote(permissions)

    default_privileges = None
    if username and user_id:
        suser = SandstormUser.query.filter_by(sandstorm_user_id=user_id).first()

        if not suser:
            if not mg_globals.app.auth:
                messages.add_message(
                    request,
                    messages.WARNING,
                    _('Sorry, authentication is disabled on this '
                      'instance.'))
                return redirect(request, 'index')

            while User.query.filter_by(username=username).count() > 0:
                username += '2'

            user = User()
            user.username = username
            user.email = ''
            user.pw_hash = unicode(getrandbits(192))

            default_privileges = [
                Privilege.query.filter(Privilege.privilege_name==u'commenter').first(),
                Privilege.query.filter(Privilege.privilege_name==u'reporter').first(),
                Privilege.query.filter(Privilege.privilege_name==u'active').first()]
        else:
            user = suser.user

        if 'admin' in permissions.split(','):
            default_privileges = [
                Privilege.query.filter(Privilege.privilege_name==u'commenter').first(),
                Privilege.query.filter(Privilege.privilege_name==u'reporter').first(),
                Privilege.query.filter(Privilege.privilege_name==u'active').first(),
                Privilege.query.filter(Privilege.privilege_name==u'admin').first(),
                Privilege.query.filter(Privilege.privilege_name==u'moderator').first(),
                Privilege.query.filter(Privilege.privilege_name==u'uploader').first()]

        if default_privileges:
            user.all_privileges += default_privileges
        user.save()

        if not suser:
            suser = SandstormUser()
            suser.user_id = user.id
            suser.sandstorm_user_id = user_id
            suser.save()

        request.session['user_id'] = unicode(user.id)
        request.session.save()

    if request.form.get('next'):
        return redirect(request, location=request.form['next'])
    else:
        return redirect(request, "index")


@allow_registration
@auth_enabled
def register(request):
    return redirect(
        request,
        'mediagoblin.plugins.sandstorm.login')
