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
from itsdangerous import BadSignature

from mediagoblin import messages
from mediagoblin.db.models import User
from mediagoblin.decorators import require_active_login
from mediagoblin.plugins.basic_auth import forms, tools
from mediagoblin.tools.crypto import get_timed_signer_url
from mediagoblin.tools.mail import email_debug_message
from mediagoblin.tools.response import redirect, render_to_response, render_404
from mediagoblin.tools.translate import pass_to_ugettext as _


def forgot_password(request):
    """
    Forgot password view

    Sends an email with an url to renew forgotten password.
    Use GET querystring parameter 'username' to pre-populate the input field
    """
    fp_form = forms.ForgotPassForm(request.form,
                                   username=request.args.get('username'))

    if not (request.method == 'POST' and fp_form.validate()):
        # Either GET request, or invalid form submitted. Display the template
        return render_to_response(request,
            'mediagoblin/plugins/basic_auth/forgot_password.html',
            {'fp_form': fp_form})

    # If we are here: method == POST and form is valid. username casing
    # has been sanitized. Store if a user was found by email. We should
    # not reveal if the operation was successful then as we don't want to
    # leak if an email address exists in the system.
    found_by_email = '@' in fp_form.username.data

    if found_by_email:
        user = User.query.filter_by(
            email=fp_form.username.data).first()
        # Don't reveal success in case the lookup happened by email address.
        success_message = _("If that email address (case sensitive!) is "
                            "registered an email has been sent with "
                            "instructions on how to change your password.")

    else:  # found by username
        user = User.query.filter_by(
            username=fp_form.username.data).first()

        if user is None:
            messages.add_message(request,
                                 messages.WARNING,
                                 _("Couldn't find someone with that username."))
            return redirect(request, 'mediagoblin.auth.forgot_password')

        success_message = _("An email has been sent with instructions "
                            "on how to change your password.")

    if user and user.has_privilege(u'active') is False:
        # Don't send reminder because user is inactive or has no verified email
        messages.add_message(request,
            messages.WARNING,
            _("Could not send password recovery email as your username is in"
              "active or your account's email address has not been verified."))

        return redirect(request, 'mediagoblin.user_pages.user_home',
                        user=user.username)

    # SUCCESS. Send reminder and return to login page
    if user:
        email_debug_message(request)
        tools.send_fp_verification_email(user, request)

    messages.add_message(request, messages.INFO, success_message)
    return redirect(request, 'mediagoblin.auth.login')


def verify_forgot_password(request):
    """
    Check the forgot-password verification and possibly let the user
    change their password because of it.
    """
    # get form data variables, and specifically check for presence of token
    formdata = _process_for_token(request)
    if not formdata['has_token']:
        return render_404(request)

    formdata_vars = formdata['vars']

    # Catch error if token is faked or expired
    try:
        token = get_timed_signer_url("mail_verification_token") \
                .loads(formdata_vars['token'], max_age=10*24*3600)
    except BadSignature:
        messages.add_message(
            request,
            messages.ERROR,
            _('The verification key or user id is incorrect.'))

        return redirect(
            request,
            'index')

    # check if it's a valid user id
    user = User.query.filter_by(id=int(token)).first()

    # no user in db
    if not user:
        messages.add_message(
            request, messages.ERROR,
            _('The user id is incorrect.'))
        return redirect(
            request, 'index')

    # check if user active and has email verified
    if user.has_privilege(u'active'):
        cp_form = forms.ChangeForgotPassForm(formdata_vars)

        if request.method == 'POST' and cp_form.validate():
            user.pw_hash = tools.bcrypt_gen_password_hash(
                cp_form.password.data)
            user.save()

            messages.add_message(
                request,
                messages.INFO,
                _("You can now log in using your new password."))
            return redirect(request, 'mediagoblin.auth.login')
        else:
            return render_to_response(
                request,
                'mediagoblin/plugins/basic_auth/change_fp.html',
                {'cp_form': cp_form})

    ## Commenting this out temporarily because I'm checking into
    ## what's going on with user.email_verified.
    ##
    ## ... if this commit lasts long enough for anyone but me (cwebber) to
    ## notice it, they should pester me to remove this or remove it
    ## themselves ;)
    #
    # if not user.email_verified:
    #     messages.add_message(
    #         request, messages.ERROR,
    #         _('You need to verify your email before you can reset your'
    #           ' password.'))

    if not user.status == 'active':
        messages.add_message(
            request, messages.ERROR,
            _('You are no longer an active user. Please contact the system'
              ' admin to reactivate your account.'))

    return redirect(
        request, 'index')


def _process_for_token(request):
    """
    Checks for tokens in formdata without prior knowledge of request method

    For now, returns whether the userid and token formdata variables exist, and
    the formdata variables in a hash. Perhaps an object is warranted?
    """
    # retrieve the formdata variables
    if request.method == 'GET':
        formdata_vars = request.GET
    else:
        formdata_vars = request.form

    formdata = {
        'vars': formdata_vars,
        'has_token': 'token' in formdata_vars}

    return formdata


@require_active_login
def change_pass(request):
    form = forms.ChangePassForm(request.form)
    user = request.user

    if request.method == 'POST' and form.validate():

        if not tools.bcrypt_check_password(
                form.old_password.data, user.pw_hash):
            form.old_password.errors.append(
                _('Wrong password'))

            return render_to_response(
                request,
                'mediagoblin/plugins/basic_auth/change_pass.html',
                {'form': form,
                 'user': user})

        # Password matches
        user.pw_hash = tools.bcrypt_gen_password_hash(
            form.new_password.data)
        user.save()

        messages.add_message(
            request, messages.SUCCESS,
            _('Your password was changed successfully'))

        return redirect(request, 'mediagoblin.edit.account')

    return render_to_response(
        request,
        'mediagoblin/plugins/basic_auth/change_pass.html',
        {'form': form,
         'user': user})
