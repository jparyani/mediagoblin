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

import uuid

from webob import exc

from mediagoblin import messages
from mediagoblin import mg_globals
from mediagoblin.util import render_to_response, redirect, render_404
from mediagoblin.util import pass_to_ugettext as _
from mediagoblin.db.util import ObjectId
from mediagoblin.auth import lib as auth_lib
from mediagoblin.auth import forms as auth_forms
from mediagoblin.auth.lib import send_verification_email


def register(request):
    """
    Your classic registration view!
    """
    # Redirects to indexpage if registrations are disabled
    if not mg_globals.app_config["allow_registration"]:
        messages.add_message(
            request,
            messages.WARNING,
            _('Sorry, registration is disabled on this instance.'))
        return redirect(request, "index")

    register_form = auth_forms.RegistrationForm(request.POST)

    if request.method == 'POST' and register_form.validate():
        # TODO: Make sure the user doesn't exist already
        username = unicode(request.POST['username'].lower())
        email = unicode(request.POST['email'].lower())
        users_with_username = request.db.User.find(
            {'username': username}).count()
        users_with_email = request.db.User.find(
            {'email': email}).count()

        extra_validation_passes = True

        if users_with_username:
            register_form.username.errors.append(
                _(u'Sorry, a user with that name already exists.'))
            extra_validation_passes = False
        if users_with_email:
            register_form.email.errors.append(
                _(u'Sorry, that email address has already been taken.'))
            extra_validation_passes = False

        if extra_validation_passes:
            # Create the user
            user = request.db.User()
            user['username'] = username
            user['email'] = email
            user['pw_hash'] = auth_lib.bcrypt_gen_password_hash(
                request.POST['password'])
            user.save(validate=True)

            # log the user in
            request.session['user_id'] = unicode(user['_id'])
            request.session.save()

            # send verification email
            send_verification_email(user, request)

            # redirect the user to their homepage... there will be a
            # message waiting for them to verify their email
            return redirect(
                request, 'mediagoblin.user_pages.user_home',
                user=user['username'])

    return render_to_response(
        request,
        'mediagoblin/auth/register.html',
        {'register_form': register_form})


def login(request):
    """
    MediaGoblin login view.

    If you provide the POST with 'next', it'll redirect to that view.
    """
    login_form = auth_forms.LoginForm(request.POST)

    login_failed = False

    if request.method == 'POST' and login_form.validate():
        user = request.db.User.one(
            {'username': request.POST['username'].lower()})

        if user and user.check_login(request.POST['password']):
            # set up login in session
            request.session['user_id'] = unicode(user['_id'])
            request.session.save()

            if request.POST.get('next'):
                return exc.HTTPFound(location=request.POST['next'])
            else:
                return redirect(request, "index")

        else:
            # Prevent detecting who's on this system by testing login
            # attempt timings
            auth_lib.fake_login_attempt()
            login_failed = True

    return render_to_response(
        request,
        'mediagoblin/auth/login.html',
        {'login_form': login_form,
         'next': request.GET.get('next') or request.POST.get('next'),
         'login_failed': login_failed,
         'allow_registration': mg_globals.app_config["allow_registration"]})


def logout(request):
    # Maybe deleting the user_id parameter would be enough?
    request.session.delete()

    return redirect(request, "index")


def verify_email(request):
    """
    Email verification view

    validates GET parameters against database and unlocks the user account, if
    you are lucky :)
    """
    # If we don't have userid and token parameters, we can't do anything; 404
    if not request.GET.has_key('userid') or not request.GET.has_key('token'):
        return render_404(request)

    user = request.db.User.find_one(
        {'_id': ObjectId(unicode(request.GET['userid']))})

    if user and user['verification_key'] == unicode(request.GET['token']):
        user['status'] = u'active'
        user['email_verified'] = True
        user.save()
        messages.add_message(
            request,
            messages.SUCCESS,
            _("Your email address has been verified. "
              "You may now login, edit your profile, and submit images!"))
    else:
        messages.add_message(
            request,
            messages.ERROR,
            _('The verification key or user id is incorrect'))

    return redirect(
        request, 'mediagoblin.user_pages.user_home',
        user=user['username'])


def resend_activation(request):
    """
    The reactivation view

    Resend the activation email.
    """
    request.user['verification_key'] = unicode(uuid.uuid4())
    request.user.save()

    send_verification_email(request.user, request)

    messages.add_message(
        request,
        messages.INFO,
        _('Resent your verification email.'))
    return redirect(
        request, 'mediagoblin.user_pages.user_home',
        user=request.user['username'])
