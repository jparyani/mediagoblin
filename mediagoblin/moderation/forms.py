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

ACTION_CHOICES = [
    (u'takeaway', _(u'Take away privilege')),
    (u'userban', _(u'Ban the user')),
    (u'sendmessage', _(u'Send the user a message')),
    (u'delete', _(u'Delete the content'))]

class MultiCheckboxField(wtforms.SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.

    code from http://wtforms.simplecodes.com/docs/1.0.4/specific_problems.html
    """
    widget = wtforms.widgets.ListWidget(prefix_label=False)
    option_widget = wtforms.widgets.CheckboxInput()


# ============ Forms for mediagoblin.moderation.user page ==================  #

class PrivilegeAddRemoveForm(wtforms.Form):
    """
    This form is used by an admin to give/take away a privilege directly from
        their user page.
    """
    privilege_name = wtforms.HiddenField('',[wtforms.validators.required()])

class BanForm(wtforms.Form):
    """
    This form is used by an admin to ban a user directly from their user page.
    """
    user_banned_until = wtforms.DateField(
        _(u'User will be banned until:'),
        format='%Y-%m-%d',
        validators=[wtforms.validators.optional()])
    why_user_was_banned = wtforms.TextAreaField(
        _(u'Why are you banning this User?'),
        validators=[wtforms.validators.optional()])

# =========== Forms for mediagoblin.moderation.report page =================  #

class ReportResolutionForm(wtforms.Form):
    """
    This form carries all the information necessary to take punitive actions
        against a user who created content that has been reported.

        :param  action_to_resolve       A list of Unicode objects representing
                                        a choice from the ACTION_CHOICES const-
                                        -ant. Every choice passed affects what
                                        punitive actions will be taken against
                                        the user.

        :param targeted_user            A HiddenField object that holds the id
                                        of the user that was reported.

        :param take_away_privileges     A list of Unicode objects which repres-
                                        -ent the privileges that are being tak-
                                        -en away. This field is optional and
                                        only relevant if u'takeaway' is in the
                                        `action_to_resolve` list.

        :param user_banned_until        A DateField object that holds the date
                                        that the user will be unbanned. This
                                        field is optional and only relevant if
                                        u'userban' is in the action_to_resolve
                                        list. If the user is being banned and
                                        this field is blank, the user is banned
                                        indefinitely.

         :param why_user_was_banned     A TextArea object that holds the
                                        reason that a user was banned, to disp-
                                        -lay to them when they try to log in.
                                        This field is optional and only relevant
                                        if u'userban' is in the
                                        `action_to_resolve` list.

        :param message_to_user          A TextArea object that holds a message
                                        which will be emailed to the user. This
                                        is only relevant if the u'sendmessage'
                                        option is in the `action_to_resolve`
                                        list.

        :param resolution_content       A TextArea object that is required for
                                        every report filed. It represents the
                                        reasons that the moderator/admin resol-
                                        -ved the report in such a way.
    """
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
        _(u'Why user was banned:'),
        validators=[wtforms.validators.optional()])
    message_to_user = wtforms.TextAreaField(
        _(u'Message to user:'),
        validators=[wtforms.validators.optional()])
    resolution_content = wtforms.TextAreaField(
        _(u'Resolution content:'))

# ======== Forms for mediagoblin.moderation.report_panel page ==============  #

class ReportPanelSortingForm(wtforms.Form):
    """
    This form is used for sorting and filtering through different reports in
    the mediagoblin.moderation.reports_panel view.

    """
    active_p = wtforms.IntegerField(
        validators=[wtforms.validators.optional()])
    closed_p = wtforms.IntegerField(
        validators=[wtforms.validators.optional()])
    reported_user = wtforms.IntegerField(
        validators=[wtforms.validators.optional()])
    reporter = wtforms.IntegerField(
        validators=[wtforms.validators.optional()])

class UserPanelSortingForm(wtforms.Form):
    """
    This form is used for sorting different reports.
    """
    p = wtforms.IntegerField(
        validators=[wtforms.validators.optional()])
