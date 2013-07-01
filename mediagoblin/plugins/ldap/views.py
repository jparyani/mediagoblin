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
from mediagoblin.auth.tools import register_user
from mediagoblin.plugins.ldap import forms
from mediagoblin.tools.response import redirect, render_to_response


def register(request):
    username = request.session.pop('username')
    if 'email' in request.session:
        email = request.session.pop('email')
    else:
        email = None
    register_form = forms.RegisterForm(request.form, username=username,
                                       email=email)

    if request.method == 'POST' and register_form.validate():
        user = register_user(request, register_form)

        if user:
            # redirect the user to their homepage... there will be a
            # message waiting for them to verify their email
            return redirect(
                request, 'mediagoblin.user_pages.user_home',
                user=user.username)

    return render_to_response(
        request,
        'mediagoblin/auth/register.html',
        {'register_form': register_form,
         'post_url': request.urlgen('mediagoblin.plugins.ldap.register')})
