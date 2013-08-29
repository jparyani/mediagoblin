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

ACTION_CHOICES = [(_(u'takeaway'),_(u'Take away privilege')),
    (_(u'userban'),_(u'Ban the user')),
    (_(u'sendmessage'),(u'Send the user a message')),
    (_(u'delete'),_(u'Delete the content'))]

class MultiCheckboxField(wtforms.SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.

    code from http://wtforms.simplecodes.com/docs/1.0.4/specific_problems.html
    """
    widget = wtforms.widgets.ListWidget(prefix_label=False)
    option_widget = wtforms.widgets.CheckboxInput()


class PrivilegeAddRemoveForm(wtforms.Form):
    privilege_name = wtforms.HiddenField('',[wtforms.validators.required()])

class BanForm(wtforms.Form):
    user_banned_until = wtforms.DateField(
        _(u'User will be banned until:'),
        format='%Y-%m-%d',
        validators=[wtforms.validators.optional()])
    why_user_was_banned = wtforms.TextAreaField(
        _(u'Why are you banning this User?'),
        validators=[wtforms.validators.optional()])

class ReportResolutionForm(wtforms.Form):
    action_to_resolve = MultiCheckboxField(
        _(u'What action will you take to resolve the report?'),
        validators=[wtforms.validators.optional()],
        choices=ACTION_CHOICES)
    targeted_user   = wtforms.HiddenField('',
        validators=[wtforms.validators.required()])
    take_away_privileges = wtforms.SelectMultipleField(
        _(u'What privileges will you take away?'),
        validators=[wtforms.validators.optional()])
    user_banned_until = wtforms.DateField(
        _(u'User will be banned until:'),
        format='%Y-%m-%d',
        validators=[wtforms.validators.optional()])
    why_user_was_banned = wtforms.TextAreaField(
        validators=[wtforms.validators.optional()])
    message_to_user = wtforms.TextAreaField(
        validators=[wtforms.validators.optional()])
    resolution_content = wtforms.TextAreaField()

