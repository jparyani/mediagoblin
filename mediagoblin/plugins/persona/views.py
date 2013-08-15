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
import json
import logging
import requests

from werkzeug.exceptions import BadRequest

from mediagoblin import messages, mg_globals
from mediagoblin.auth.tools import register_user
from mediagoblin.decorators import (auth_enabled, allow_registration,
                                    require_active_login)
from mediagoblin.tools.response import render_to_response, redirect
from mediagoblin.tools.translate import pass_to_ugettext as _
from mediagoblin.plugins.persona import forms
from mediagoblin.plugins.persona.models import PersonaUserEmails

_log = logging.getLogger(__name__)


def _get_response(request):
    if 'assertion' not in request.form:
        _log.debug('assertion not in request.form')
        raise BadRequest()

    data = {'assertion': request.form['assertion'],
            'audience': request.urlgen('index', qualified=True)}
    resp = requests.post('https://verifier.login.persona.org/verify',
                         data=data, verify=True)

    if resp.ok:
        verification_data = json.loads(resp.content)

        if verification_data['status'] == 'okay':
            return verification_data['email']

    return None


@auth_enabled
def login(request):
    if request.method == 'GET':
        return redirect(request, 'mediagoblin.auth.login')

    email = _get_response(request)
    if email:
        query = PersonaUserEmails.query.filter_by(
            persona_email=email
        ).first()
        user = query.user if query else None

        if user:
            request.session['user_id'] = unicode(user.id)
            request.session.save()

            return redirect(request, "index")

        else:
            if not mg_globals.app.auth:
                messages.add_message(
                    request,
                    messages.WARNING,
                    _('Sorry, authentication is disabled on this instance.'))

                return redirect(request, 'index')

            register_form = forms.RegistrationForm(email=email,
                                                   persona_email=email)
            return render_to_response(
                request,
                'mediagoblin/auth/register.html',
                {'register_form': register_form,
                'post_url': request.urlgen(
                    'mediagoblin.plugins.persona.register')})

    return redirect(request, 'mediagoblin.auth.login')


@allow_registration
@auth_enabled
def register(request):
    if request.method == 'GET':
        # Need to connect to persona before registering a user. If method is
        # 'GET', then this page was acessed without logging in first.
        return redirect(request, 'mediagoblin.auth.login')
    register_form = forms.RegistrationForm(request.form)

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
         'post_url': request.urlgen('mediagoblin.plugins.persona.register')})


@require_active_login
def edit(request):
    form = forms.EditForm(request.form)

    if request.method == 'POST' and form.validate():
        query = PersonaUserEmails.query.filter_by(
            persona_email=form.email.data)
        user = query.first().user if query.first() else None

        if user and user.id == int(request.user.id):
            count = len(user.persona_emails)

            if count > 1 or user.pw_hash:
                # User has more then one Persona email or also has a password.
                query.first().delete()

                messages.add_message(
                    request,
                    messages.SUCCESS,
                    _('The Persona email address was successfully removed.'))

                return redirect(request, 'mediagoblin.edit.account')

            elif not count > 1:
                form.email.errors.append(
                    _("You can't delete your only Persona email address unless"
                      " you have a password set."))

        else:
            form.email.errors.append(
                _('That Persona email address is not registered to this'
                  ' account.'))

    return render_to_response(
        request,
        'mediagoblin/plugins/persona/edit.html',
        {'form': form,
         'edit_persona': True})


@require_active_login
def add(request):
    if request.method == 'GET':
        return redirect(request, 'mediagoblin.plugins.persona.edit')

    email = _get_response(request)

    if email:
        query = PersonaUserEmails.query.filter_by(
            persona_email=email
        ).first()
    user_exists = query.user if query else None

    if user_exists:
        messages.add_message(
            request,
            messages.WARNING,
            _('Sorry, an account is already registered with that Persona'
              ' email address.'))
        return redirect(request, 'mediagoblin.plugins.persona.edit')

    else:
        # Save the Persona Email to the user
        new_entry = PersonaUserEmails()
        new_entry.persona_email = email
        new_entry.user_id = request.user.id
        new_entry.save()

        messages.add_message(
            request,
            messages.SUCCESS,
            _('Your Person email address was saved successfully.'))

        return redirect(request, 'mediagoblin.edit.account')
