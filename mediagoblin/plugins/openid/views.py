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
from openid.consumer import consumer
from openid.consumer.discover import DiscoveryFailure
from openid.extensions.sreg import SRegRequest, SRegResponse

from mediagoblin import mg_globals, messages
from mediagoblin.db.models import User
from mediagoblin.decorators import (auth_enabled, allow_registration,
                                    require_active_login)
from mediagoblin.tools.response import redirect, render_to_response
from mediagoblin.tools.translate import pass_to_ugettext as _
from mediagoblin.plugins.openid import forms as auth_forms
from mediagoblin.plugins.openid.models import OpenIDUserURL
from mediagoblin.plugins.openid.store import SQLAlchemyOpenIDStore
from mediagoblin.auth.tools import register_user


def _start_verification(request, form, return_to, sreg=True):
    """
    Start OpenID Verification.

    Returns False if verification fails, otherwise, will return either a
    redirect or render_to_response object
    """
    openid_url = form.openid.data
    c = consumer.Consumer(request.session, SQLAlchemyOpenIDStore())

    # Try to discover provider
    try:
        auth_request = c.begin(openid_url)
    except DiscoveryFailure:
        # Discovery failed, return to login page
        form.openid.errors.append(
            _('Sorry, the OpenID server could not be found'))

        return False

    host = 'http://' + request.host

    if sreg:
        # Ask provider for email and nickname
        auth_request.addExtension(SRegRequest(required=['email', 'nickname']))

    # Do we even need this?
    if auth_request is None:
        form.openid.errors.append(
            _('No OpenID service was found for %s' % openid_url))

    elif auth_request.shouldSendRedirect():
        # Begin the authentication process as a HTTP redirect
        redirect_url = auth_request.redirectURL(
            host, return_to)

        return redirect(
            request, location=redirect_url)

    else:
        # Send request as POST
        form_html = auth_request.htmlMarkup(
            host, host + return_to,
            # Is this necessary?
            form_tag_attrs={'id': 'openid_message'})

        # Beware: this renders a template whose content is a form
        # and some javascript to submit it upon page load.  Non-JS
        # users will have to click the form submit button to
        # initiate OpenID authentication.
        return render_to_response(
            request,
            'mediagoblin/plugins/openid/request_form.html',
            {'html': form_html})

    return False


def _finish_verification(request):
    """
    Complete OpenID Verification Process.

    If the verification failed, will return false, otherwise, will return
    the response
    """
    c = consumer.Consumer(request.session, SQLAlchemyOpenIDStore())

    # Check the response from the provider
    response = c.complete(request.args, request.base_url)
    if response.status == consumer.FAILURE:
        messages.add_message(
            request,
            messages.WARNING,
            _('Verification of %s failed: %s' %
                (response.getDisplayIdentifier(), response.message)))

    elif response.status == consumer.SUCCESS:
        # Verification was successfull
        return response

    elif response.status == consumer.CANCEL:
        # Verification canceled
        messages.add_message(
            request,
            messages.WARNING,
            _('Verification cancelled'))

    return False


def _response_email(response):
    """ Gets the email from the OpenID providers response"""
    sreg_response = SRegResponse.fromSuccessResponse(response)
    if sreg_response and 'email' in sreg_response:
        return sreg_response.data['email']
    return None


def _response_nickname(response):
    """ Gets the nickname from the OpenID providers response"""
    sreg_response = SRegResponse.fromSuccessResponse(response)
    if sreg_response and 'nickname' in sreg_response:
        return sreg_response.data['nickname']
    return None


@auth_enabled
def login(request):
    """OpenID Login View"""
    login_form = auth_forms.LoginForm(request.form)
    allow_registration = mg_globals.app_config["allow_registration"]

    # Can't store next in request.GET because of redirects to OpenID provider
    # Store it in the session
    next = request.GET.get('next')
    request.session['next'] = next

    login_failed = False

    if request.method == 'POST' and login_form.validate():
        return_to = request.urlgen(
            'mediagoblin.plugins.openid.finish_login')

        success = _start_verification(request, login_form, return_to)

        if success:
            return success

        login_failed = True

    return render_to_response(
        request,
        'mediagoblin/plugins/openid/login.html',
        {'login_form': login_form,
        'next': request.session.get('next'),
        'login_failed': login_failed,
        'post_url': request.urlgen('mediagoblin.plugins.openid.login'),
        'allow_registration': allow_registration})


@auth_enabled
def finish_login(request):
    """Complete OpenID Login Process"""
    response = _finish_verification(request)

    if not response:
        # Verification failed, redirect to login page.
        return redirect(request, 'mediagoblin.plugins.openid.login')

    # Verification was successfull
    query = OpenIDUserURL.query.filter_by(
        openid_url=response.identity_url,
        ).first()
    user = query.user if query else None

    if user:
        # Set up login in session
        request.session['user_id'] = unicode(user.id)
        request.session.save()

        if request.session.get('next'):
            return redirect(request, location=request.session.pop('next'))
        else:
            return redirect(request, "index")
    else:
        # No user, need to register
        if not mg_globals.app.auth:
            messages.add_message(
                request,
                messages.WARNING,
                _('Sorry, authentication is disabled on this instance.'))
            return redirect(request, 'index')

        # Get email and nickname from response
        email = _response_email(response)
        username = _response_nickname(response)

        register_form = auth_forms.RegistrationForm(request.form,
                                                openid=response.identity_url,
                                                email=email,
                                                username=username)
        return render_to_response(
            request,
            'mediagoblin/auth/register.html',
            {'register_form': register_form,
            'post_url': request.urlgen('mediagoblin.plugins.openid.register')})


@allow_registration
@auth_enabled
def register(request):
    """OpenID Registration View"""
    if request.method == 'GET':
        # Need to connect to openid provider before registering a user to
        # get the users openid url. If method is 'GET', then this page was
        # acessed without logging in first.
        return redirect(request, 'mediagoblin.plugins.openid.login')

    register_form = auth_forms.RegistrationForm(request.form)

    if register_form.validate():
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
         'post_url': request.urlgen('mediagoblin.plugins.openid.register')})


@require_active_login
def start_edit(request):
    """Starts the process of adding an openid url to a users account"""
    form = auth_forms.LoginForm(request.form)

    if request.method == 'POST' and form.validate():
        query = OpenIDUserURL.query.filter_by(
            openid_url=form.openid.data
            ).first()
        user = query.user if query else None

        if not user:
            return_to = request.urlgen('mediagoblin.plugins.openid.finish_edit')
            success = _start_verification(request, form, return_to, False)

            if success:
                return success
        else:
            form.openid.errors.append(
                _('Sorry, an account is already registered to that OpenID.'))

    return render_to_response(
        request,
        'mediagoblin/plugins/openid/add.html',
        {'form': form,
         'post_url': request.urlgen('mediagoblin.plugins.openid.edit')})


@require_active_login
def finish_edit(request):
    """Finishes the process of adding an openid url to a user"""
    response = _finish_verification(request)

    if not response:
        # Verification failed, redirect to add openid page.
        return redirect(request, 'mediagoblin.plugins.openid.edit')

    # Verification was successfull
    query = OpenIDUserURL.query.filter_by(
        openid_url=response.identity_url,
        ).first()
    user_exists = query.user if query else None

    if user_exists:
        # user exists with that openid url, redirect back to edit page
        messages.add_message(
            request,
            messages.WARNING,
            _('Sorry, an account is already registered to that OpenID.'))
        return redirect(request, 'mediagoblin.plugins.openid.edit')

    else:
        # Save openid to user
        user = User.query.filter_by(
            id=request.session['user_id']
            ).first()

        new_entry = OpenIDUserURL()
        new_entry.openid_url = response.identity_url
        new_entry.user_id = user.id
        new_entry.save()

        messages.add_message(
            request,
            messages.SUCCESS,
            _('Your OpenID url was saved successfully.'))

        return redirect(request, 'mediagoblin.edit.account')


@require_active_login
def delete_openid(request):
    """View to remove an openid from a users account"""
    form = auth_forms.LoginForm(request.form)

    if request.method == 'POST' and form.validate():
        # Check if a user has this openid
        query = OpenIDUserURL.query.filter_by(
            openid_url=form.openid.data
            )
        user = query.first().user if query.first() else None

        if user and user.id == int(request.session['user_id']):
            count = len(user.openid_urls)
            if not count > 1 and not user.pw_hash:
                # Make sure the user has a pw or another OpenID
                messages.add_message(
                    request,
                    messages.WARNING,
                    _("You can't delete your only OpenID URL unless you"
                        " have a password set"))
        elif user:
            # There is a user, but not the same user who is logged in
            form.openid.errors.append(
                _('That OpenID is not registered to this account.'))

        if not form.errors and not request.session['messages']:
            # Okay to continue with deleting openid
            return_to = request.urlgen(
                'mediagoblin.plugins.openid.finish_delete')
            success = _start_verification(request, form, return_to, False)

            if success:
                return success

    return render_to_response(
        request,
        'mediagoblin/plugins/openid/delete.html',
        {'form': form,
         'post_url': request.urlgen('mediagoblin.plugins.openid.delete')})


@require_active_login
def finish_delete(request):
    """Finishes the deletion of an OpenID from an user's account"""
    response = _finish_verification(request)

    if not response:
        # Verification failed, redirect to delete openid page.
        return redirect(request, 'mediagoblin.plugins.openid.delete')

    query = OpenIDUserURL.query.filter_by(
        openid_url=response.identity_url
        )
    user = query.first().user if query.first() else None

    # Need to check this again because of generic openid urls such as google's
    if user and user.id == int(request.session['user_id']):
        count = len(user.openid_urls)
        if count > 1 or user.pw_hash:
            # User has more then one openid or also has a password.
            query.first().delete()

            messages.add_message(
                request,
                messages.SUCCESS,
                _('OpenID was successfully removed.'))

            return redirect(request, 'mediagoblin.edit.account')

        elif not count > 1:
            messages.add_message(
                request,
                messages.WARNING,
                _("You can't delete your only OpenID URL unless you have a "
                    "password set"))

            return redirect(request, 'mediagoblin.plugins.openid.delete')

    else:
        messages.add_message(
            request,
            messages.WARNING,
            _('That OpenID is not registered to this account.'))

        return redirect(request, 'mediagoblin.plugins.openid.delete')
