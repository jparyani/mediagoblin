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
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _

ACTION_CHOICES = [(_(u'takeaway'),_('Take away privilege')),
    (_(u'userban'),_('Ban the user')),
    (_(u'closereport'),_('Close the report without taking an action'))]

class PrivilegeAddRemoveForm(wtforms.Form):
    giving_privilege = wtforms.HiddenField('',[wtforms.validators.required()])
    privilege_name = wtforms.HiddenField('',[wtforms.validators.required()])

class ReportResolutionForm(wtforms.Form):
    action_to_resolve = wtforms.RadioField(
        _('What action will you take to resolve this report'), 
        validators=[wtforms.validators.required()],
        choices=ACTION_CHOICES)
    targeted_user   = wtforms.HiddenField('',
        validators=[wtforms.validators.required()])
    user_banned_until = wtforms.DateField(
        _('User will be banned until:'),
        format='%Y-%m-%d',
        validators=[wtforms.validators.optional()])
    resolution_content = wtforms.TextAreaField()

