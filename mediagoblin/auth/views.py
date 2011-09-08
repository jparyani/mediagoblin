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

import uuid
import datetime

from webob import exc

from mediagoblin import messages
from mediagoblin import mg_globals
from mediagoblin.util import render_to_response, redirect, render_404
from mediagoblin.util import pass_to_ugettext as _
from mediagoblin.db.util import ObjectId, InvalidId
from mediagoblin.auth import lib as auth_lib
from mediagoblin.auth import forms as auth_forms
from mediagoblin.auth.lib import send_verification_email, \
                                 send_fp_verification_email


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

        users_with_username = request.db.User.find(
            {'username': request.POST['username'].lower()}).count()
        users_with_email = request.db.User.find(
            {'email': request.POST['email'].lower()}).count()

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
            user['username'] = request.POST['username'].lower()
            user['email'] = request.POST['email'].lower()
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
        user[u'status'] = u'active'
        user[u'email_verified'] = True
        user[u'verification_key'] = None

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
    request.user[u'verification_key'] = unicode(uuid.uuid4())
    request.user.save()

    send_verification_email(request.user, request)

    messages.add_message(
        request,
        messages.INFO,
        _('Resent your verification email.'))
    return redirect(
        request, 'mediagoblin.user_pages.user_home',
        user=request.user['username'])


def forgot_password(request):
    """
    Forgot password view

    Sends an email whit an url to renew forgoten password
    """
    fp_form = auth_forms.ForgotPassForm(request.POST)

    if request.method == 'POST' and fp_form.validate():
        # '$or' not available till mongodb 1.5.3
        user = request.db.User.find_one(
            {'username': request.POST['username']})
        if not user:
            user = request.db.User.find_one(
                {'email': request.POST['username']})

        if user:
            if user['email_verified'] and user['status'] == 'active':
                user[u'fp_verification_key'] = unicode(uuid.uuid4())
                user[u'fp_token_expire'] = datetime.datetime.now() + \
                                          datetime.timedelta(days=10)
                user.save()

                send_fp_verification_email(user, request)
            else:
                # special case... we can't send the email because the
                # username is inactive / hasn't verified their email
                messages.add_message(
                    request,
                    messages.WARNING,
                    _("Could not send password recovery email as "
                      "your username is inactive or your account's "
                      "email address has not been verified."))

                return redirect(
                    request, 'mediagoblin.user_pages.user_home',
                    user=user['username'])


        # do not reveal whether or not there is a matching user, just move along
        return redirect(request, 'mediagoblin.auth.fp_email_sent')

    return render_to_response(
        request,
        'mediagoblin/auth/forgot_password.html',
        {'fp_form': fp_form})


def verify_forgot_password(request):
    # get session variables, and specifically check for presence of token
    mysession = _process_for_token(request)
    if not mysession['has_userid_and_token']:
        return render_404(request)

    session_token = mysession['vars']['token']
    session_userid = mysession['vars']['userid']
    session_vars = mysession['vars']

    # check if it's a valid Id
    try:
        user = request.db.User.find_one(
                                     {'_id': ObjectId(unicode(session_userid))})
    except InvalidId:
        return render_404(request)

    # check if we have a real user and correct token
    if ((user and user['fp_verification_key'] and
         user['fp_verification_key'] == unicode(session_token) and
         datetime.datetime.now() < user['fp_token_expire']
         and user['email_verified'] and user['status'] == 'active')):

        cp_form = auth_forms.ChangePassForm(session_vars)

        if request.method == 'POST' and cp_form.validate():
            user[u'pw_hash'] = auth_lib.bcrypt_gen_password_hash(
                request.POST['password'])
            user[u'fp_verification_key'] = None
            user[u'fp_token_expire'] = None
            user.save()

            return redirect(request, 'mediagoblin.auth.fp_changed_success')
        else:
            return render_to_response(
                request,
                'mediagoblin/auth/change_fp.html',
                {'cp_form': cp_form})

    # in case there is a valid id but no user whit that id in the db
    # or the token expired
    else:
        return render_404(request)


def _process_for_token(request):
    """
    Checks for tokens in session without prior knowledge of request method

    For now, returns whether the userid and token session variables exist, and
    the session variables in a hash. Perhaps an object is warranted?
    """
    # retrieve the session variables
    if request.method == 'GET':
        session_vars = request.GET
    else:
        session_vars = request.POST

    mysession = {
        'vars': session_vars,
        'has_userid_and_token':
            session_vars.has_key('userid') and session_vars.has_key('token')}

    return mysession
