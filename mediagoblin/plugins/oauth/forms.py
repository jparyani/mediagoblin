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

import wtforms

from urlparse import urlparse

from mediagoblin.tools.extlib.wtf_html5 import URLField
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _


class AuthorizationForm(wtforms.Form):
    client_id = wtforms.HiddenField(u'',
                                    validators=[wtforms.validators.Required()])
    next = wtforms.HiddenField(u'', validators=[wtforms.validators.Required()])
    allow = wtforms.SubmitField(_(u'Allow'))
    deny = wtforms.SubmitField(_(u'Deny'))


class ClientRegistrationForm(wtforms.Form):
    name = wtforms.TextField(_('Name'), [wtforms.validators.Required()],
            description=_('The name of the OAuth client'))
    description = wtforms.TextAreaField(_('Description'),
            [wtforms.validators.Length(min=0, max=500)],
            description=_('''This will be visible to users allowing your
                application to authenticate as them.'''))
    type = wtforms.SelectField(_('Type'),
            [wtforms.validators.Required()],
            choices=[
                ('confidential', 'Confidential'),
                ('public', 'Public')],
            description=_('''<strong>Confidential</strong> - The client can
                make requests to the GNU MediaGoblin instance that can not be
                intercepted by the user agent (e.g. server-side client).<br />
                <strong>Public</strong> - The client can't make confidential
                requests to the GNU MediaGoblin instance (e.g. client-side
                JavaScript client).'''))

    redirect_uri = URLField(_('Redirect URI'),
            [wtforms.validators.Optional(), wtforms.validators.URL()],
            description=_('''The redirect URI for the applications, this field
            is <strong>required</strong> for public clients.'''))

    def __init__(self, *args, **kw):
        wtforms.Form.__init__(self, *args, **kw)

    def validate(self):
        if not wtforms.Form.validate(self):
            return False

        if self.type.data == 'public' and not self.redirect_uri.data:
            self.redirect_uri.errors.append(
                _('This field is required for public clients'))
            return False

        return True
