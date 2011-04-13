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

from mediagoblin.auth import lib as auth_lib
from mediagoblin.auth import forms as auth_forms


def register(request):
    """
    Your classic registration view!
    """
    register_form = auth_forms.RegistrationForm(request.POST)

    if request.method == 'POST' and register_form.validate():
        # TODO: Make sure the user doesn't exist already
        users_with_username = \
            request.db.User.find({'username': request.POST['username']}).count()

        if users_with_username:
            register_form.username.errors.append(
                u'Sorry, a user with that name already exists.')

        else:
            # Create the user
            entry = request.db.User()
            entry['username'] = request.POST['username']
            entry['email'] = request.POST['email']
            entry['pw_hash'] = auth_lib.bcrypt_gen_password_hash(
                request.POST['password'])
            entry.save(validate=True)

            # TODO: Send email authentication request

            # Redirect to register_success
            return exc.HTTPFound(
                location=request.urlgen("mediagoblin.auth.register_success"))

    # render
    template = request.template_env.get_template(
        'mediagoblin/auth/register.html')
    return Response(
        template.render(
            {'request': request,
             'register_form': register_form}))


def register_success(request):
    template = request.template_env.get_template(
        'mediagoblin/auth/register_success.html')
    return Response(
        template.render(
            {'request': request}))


def login(request):
    """
    MediaGoblin login view.

    If you provide the POST with 'next', it'll redirect to that view.
    """
    login_form = auth_forms.LoginForm(request.POST)

    login_failed = False

    if request.method == 'POST' and login_form.validate():
        user = request.db.User.one(
            {'username': request.POST['username']})

        if user and user.check_login(request.POST['password']):
            # set up login in session
            request.session['user_id'] = unicode(user['_id'])
            request.session.save()

            if request.POST.has_key('next'):
                return exc.HTTPFound(location=request.POST['next'])
            else:
                return exc.HTTPFound(
                    location=request.urlgen("index"))

        else:
            # Prevent detecting who's on this system by testing login
            # attempt timings
            auth_lib.fake_login_attempt()
            login_failed = True

    # render
    template = request.template_env.get_template(
        'mediagoblin/auth/login.html')
    return Response(
        template.render(
            {'request': request,
             'login_form': login_form,
             'next': request.GET.get('next') or request.POST.get('next'),
             'login_failed': login_failed}))


def logout(request):
    # Maybe deleting the user_id parameter would be enough?
    request.session.delete()
    
    return exc.HTTPFound(
        location=request.urlgen("index"))
