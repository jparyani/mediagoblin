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


@auth_enabled
def login(request):
    login_failed = False

    username = request.headers.get('X-SANDSTORM-USERNAME', None)
    user_id = request.headers.get('X-SANDSTORM-USER-ID', None)

    if username and user_id:
        user = User.query.filter_by(
            pw_hash=user_id).first()

        if user:
            # set up login in session
            request.session['user_id'] = unicode(user.id)
            request.session.save()

            if request.form.get('next'):
                return redirect(request, location=request.form['next'])
            else:
                return redirect(request, "index")
        else:
            if not mg_globals.app.auth:
                messages.add_message(
                    request,
                    messages.WARNING,
                    _('Sorry, authentication is disabled on this '
                      'instance.'))
                return redirect(request, 'index')

            user = User()
            user.username = username
            user.email = ''
            user.pw_hash = user_id

            default_privileges = [
                Privilege.query.filter(Privilege.privilege_name==u'commenter').first(),
                Privilege.query.filter(Privilege.privilege_name==u'admin').first(),
                Privilege.query.filter(Privilege.privilege_name==u'active').first(),
                Privilege.query.filter(Privilege.privilege_name==u'uploader').first(),
                Privilege.query.filter(Privilege.privilege_name==u'reporter').first()]
            user.all_privileges += default_privileges

            user.save()

            request.session['user_id'] = unicode(user.id)
            request.session.save()

            if request.form.get('next'):
                return redirect(request, location=request.form['next'])
            else:
                return redirect(request, "index")

    login_failed = True

    return render_to_response(
        request,
        'mediagoblin/auth/login.html',
        {'login_form': login_form,
         'next': request.GET.get('next') or request.form.get('next'),
         'login_failed': login_failed,
         'post_url': request.urlgen('mediagoblin.plugins.ldap.login'),
         'allow_registration': mg_globals.app_config["allow_registration"]})


@allow_registration
@auth_enabled
def register(request):
    return redirect(
        request,
        'mediagoblin.plugins.sandstorm.login')
