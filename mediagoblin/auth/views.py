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

import uuid

from mediagoblin import messages, mg_globals
from mediagoblin.db.models import User
from mediagoblin.tools.response import render_to_response, redirect, render_404
from mediagoblin.tools.translate import pass_to_ugettext as _
from mediagoblin.auth import lib as auth_lib
from mediagoblin.auth.lib import send_verification_email
import mediagoblin.auth as auth


def email_debug_message(request):
    """
    If the server is running in email debug mode (which is
    the current default), give a debug message to the user
    so that they have an idea where to find their email.
    """
    if mg_globals.app_config['email_debug_mode']:
        # DEBUG message, no need to translate
        messages.add_message(request, messages.DEBUG,
            u"This instance is running in email debug mode. "
            u"The email will be on the console of the server process.")


def register(request):
    """The registration view.

    Note that usernames will always be lowercased. Email domains are lowercased while
    the first part remains case-sensitive.
    """
    # Redirects to indexpage if registrations are disabled or no authentication
    # is enabled
    if not mg_globals.app_config["allow_registration"] or not mg_globals.app.auth:
        messages.add_message(
            request,
            messages.WARNING,
            _('Sorry, registration is disabled on this instance.'))
        return redirect(request, "index")

    register_form = auth.get_registration_form(request)

    if request.method == 'POST' and register_form.validate():
        # TODO: Make sure the user doesn't exist already
        extra_validation_passes = auth.extra_validation(register_form)

        if extra_validation_passes:
            # Create the user
            user = auth.create_user(register_form)

            # log the user in
            request.session['user_id'] = unicode(user.id)
            request.session.save()

            # send verification email
            email_debug_message(request)
            send_verification_email(user, request)

            # redirect the user to their homepage... there will be a
            # message waiting for them to verify their email
            return redirect(
                request, 'mediagoblin.user_pages.user_home',
                user=user.username)

    return render_to_response(
        request,
        'mediagoblin/auth/register.html',
        {'register_form': register_form})


def login(request):
    """
    MediaGoblin login view.

    If you provide the POST with 'next', it'll redirect to that view.
    """
    # Redirects to index page if no authentication is enabled
    if not mg_globals.app.auth:
        messages.add_message(
            request,
            messages.WARNING,
            _('Sorry, authentication is disabled on this instance.'))
        return redirect(request, 'index')

    login_form = auth.get_login_form(request)

    login_failed = False

    if request.method == 'POST':
        if login_form.validate():
            user = auth.get_user(login_form)

            if user and auth.check_login(user, login_form.password.data):
                # set up login in session
                request.session['user_id'] = unicode(user.id)
                request.session.save()

                if request.form.get('next'):
                    return redirect(request, location=request.form['next'])
                else:
                    return redirect(request, "index")

            # Some failure during login occured if we are here!
            # Prevent detecting who's on this system by testing login
            # attempt timings
            auth_lib.fake_login_attempt()
            login_failed = True

    return render_to_response(
        request,
        'mediagoblin/auth/login.html',
        {'login_form': login_form,
         'next': request.GET.get('next') or request.form.get('next'),
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
    if not 'userid' in request.GET or not 'token' in request.GET:
        return render_404(request)

    user = User.query.filter_by(id=request.args['userid']).first()

    if user and user.verification_key == unicode(request.GET['token']):
        user.status = u'active'
        user.email_verified = True
        user.verification_key = None

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

    if request.user.email_verified:
        messages.add_message(
            request,
            messages.ERROR,
            _("You've already verified your email address!"))

        return redirect(request, "mediagoblin.user_pages.user_home", user=request.user['username'])

    request.user.verification_key = unicode(uuid.uuid4())
    request.user.save()

    email_debug_message(request)
    send_verification_email(request.user, request)

    messages.add_message(
        request,
        messages.INFO,
        _('Resent your verification email.'))
    return redirect(
        request, 'mediagoblin.user_pages.user_home',
        user=request.user.username)
