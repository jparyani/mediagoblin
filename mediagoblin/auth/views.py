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

import six

from itsdangerous import BadSignature

from mediagoblin import messages, mg_globals
from mediagoblin.db.models import User, Privilege
from mediagoblin.tools.crypto import get_timed_signer_url
from mediagoblin.decorators import auth_enabled, allow_registration
from mediagoblin.tools.response import render_to_response, redirect, render_404
from mediagoblin.tools.translate import pass_to_ugettext as _
from mediagoblin.tools.mail import email_debug_message
from mediagoblin.tools.pluginapi import hook_handle
from mediagoblin.auth.tools import (send_verification_email, register_user,
                                    check_login_simple)


@allow_registration
@auth_enabled
def register(request):
    """The registration view.

    Note that usernames will always be lowercased. Email domains are lowercased while
    the first part remains case-sensitive.
    """
    if 'pass_auth' not in request.template_env.globals:
        redirect_name = hook_handle('auth_no_pass_redirect')
        if redirect_name:
            return redirect(request, 'mediagoblin.plugins.{0}.register'.format(
                redirect_name))
        else:
            return redirect(request, 'index')

    register_form = hook_handle("auth_get_registration_form", request)

    if request.method == 'POST' and register_form.validate():
        # TODO: Make sure the user doesn't exist already
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
         'post_url': request.urlgen('mediagoblin.auth.register')})


@auth_enabled
def login(request):
    """
    MediaGoblin login view.

    If you provide the POST with 'next', it'll redirect to that view.
    """
    if 'pass_auth' not in request.template_env.globals:
        redirect_name = hook_handle('auth_no_pass_redirect')
        if redirect_name:
            return redirect(request, 'mediagoblin.plugins.{0}.login'.format(
                redirect_name))
        else:
            return redirect(request, 'index')

    login_form = hook_handle("auth_get_login_form", request)

    login_failed = False

    if request.method == 'POST':

        if login_form.validate():
            user = check_login_simple(
                login_form.username.data,
                login_form.password.data)

            if user:
                # set up login in session
                if login_form.stay_logged_in.data:
                    request.session['stay_logged_in'] = True
                request.session['user_id'] = six.text_type(user.id)
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
         'post_url': request.urlgen('mediagoblin.auth.login'),
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
    if not 'token' in request.GET:
        return render_404(request)

    # Catch error if token is faked or expired
    try:
        token = get_timed_signer_url("mail_verification_token") \
                .loads(request.GET['token'], max_age=10*24*3600)
    except BadSignature:
        messages.add_message(
            request,
            messages.ERROR,
            _('The verification key or user id is incorrect.'))

        return redirect(
            request,
            'index')

    user = User.query.filter_by(id=int(token)).first()

    if user and user.has_privilege(u'active') is False:
        user.verification_key = None
        user.all_privileges.append(
            Privilege.query.filter(
            Privilege.privilege_name==u'active').first())

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
        user=user.username)


def resend_activation(request):
    """
    The reactivation view

    Resend the activation email.
    """

    if request.user is None:
        messages.add_message(
            request,
            messages.ERROR,
            _('You must be logged in so we know who to send the email to!'))

        return redirect(request, 'mediagoblin.auth.login')

    if request.user.has_privilege(u'active'):
        messages.add_message(
            request,
            messages.ERROR,
            _("You've already verified your email address!"))

        return redirect(request, "mediagoblin.user_pages.user_home", user=request.user['username'])

    email_debug_message(request)
    send_verification_email(request.user, request)

    messages.add_message(
        request,
        messages.INFO,
        _('Resent your verification email.'))
    return redirect(
        request, 'mediagoblin.user_pages.user_home',
        user=request.user.username)
