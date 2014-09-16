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

from mediagoblin import mg_globals
from mediagoblin.db.models import User, Privilege, UserBan
from mediagoblin.db.base import Session
from mediagoblin.tools.mail import send_email
from mediagoblin.tools.response import redirect
from datetime import datetime
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _


def take_punitive_actions(request, form, report, user):
    message_body = ''

    # The bulk of this action is running through all of the different
    # punitive actions that a moderator could take.
    if u'takeaway' in form.action_to_resolve.data:
        for privilege_name in form.take_away_privileges.data:
            take_away_privileges(user.username, privilege_name)
            form.resolution_content.data += \
                _(u"\n{mod} took away {user}\'s {privilege} privileges.").format(
                    mod=request.user.username,
                    user=user.username,
                    privilege=privilege_name)

    # If the moderator elects to ban the user, a new instance of user_ban
    # will be created.
    if u'userban' in form.action_to_resolve.data:
        user_ban = ban_user(form.targeted_user.data,
            expiration_date=form.user_banned_until.data,
            reason=form.why_user_was_banned.data)
        Session.add(user_ban)
        form.resolution_content.data += \
            _(u"\n{mod} banned user {user} {expiration_date}.").format(
                mod=request.user.username,
                user=user.username,
                expiration_date = (
                _("until {date}").format(date=form.user_banned_until.data)
                    if form.user_banned_until.data
                    else _("indefinitely")
                    )
            )

    # If the moderator elects to send a warning message. An email will be
    # sent to the email address given at sign up
    if u'sendmessage' in form.action_to_resolve.data:
        message_body = form.message_to_user.data
        form.resolution_content.data += \
            _(u"\n{mod} sent a warning email to the {user}.").format(
                mod=request.user.username,
                user=user.username)

    if u'delete' in form.action_to_resolve.data and \
        report.is_comment_report():
            deleted_comment = report.comment
            Session.delete(deleted_comment)
            form.resolution_content.data += \
                _(u"\n{mod} deleted the comment.").format(
                    mod=request.user.username)
    elif u'delete' in form.action_to_resolve.data and \
        report.is_media_entry_report():
            deleted_media = report.media_entry
            deleted_media.delete()
            form.resolution_content.data += \
                _(u"\n{mod} deleted the media entry.").format(
                    mod=request.user.username)
    report.archive(
        resolver_id=request.user.id,
        resolved=datetime.now(),
        result=form.resolution_content.data)

    Session.add(report)
    Session.commit()
    if message_body:
        send_email(
            mg_globals.app_config['email_sender_address'],
            [user.email],
            _('Warning from')+ '- {moderator} '.format(
                moderator=request.user.username),
            message_body)

    return redirect(
        request,
        'mediagoblin.moderation.users_detail',
        user=user.username)


def take_away_privileges(user,*privileges):
    """
    Take away all of the privileges passed as arguments.

        :param user             A Unicode object representing the target user's
                                User.username value.

        :param privileges       A variable number of Unicode objects describing
                                the privileges being taken away.


        :returns True           If ALL of the privileges were taken away
                                successfully.

        :returns False          If ANY of the privileges were not taken away
                                successfully. This means the user did not have
                                (one of) the privilege(s) to begin with.
    """
    if len(privileges) == 1:
        privilege = Privilege.query.filter(
            Privilege.privilege_name==privileges[0]).first()
        user = User.query.filter(
            User.username==user).first()
        if privilege in user.all_privileges:
            user.all_privileges.remove(privilege)
            return True
        return False

    elif len(privileges) > 1:
        return (take_away_privileges(user, privileges[0]) and \
            take_away_privileges(user, *privileges[1:]))

def give_privileges(user,*privileges):
    """
    Take away all of the privileges passed as arguments.

        :param user             A Unicode object representing the target user's
                                User.username value.

        :param privileges       A variable number of Unicode objects describing
                                the privileges being granted.


        :returns True           If ALL of the privileges were granted successf-
                                -ully.

        :returns False          If ANY of the privileges were not granted succ-
                                essfully. This means the user already had (one
                                of) the privilege(s) to begin with.
    """
    if len(privileges) == 1:
        privilege = Privilege.query.filter(
            Privilege.privilege_name==privileges[0]).first()
        user = User.query.filter(
            User.username==user).first()
        if privilege not in user.all_privileges:
            user.all_privileges.append(privilege)
            return True
        return False

    elif len(privileges) > 1:
        return (give_privileges(user, privileges[0]) and \
            give_privileges(user, *privileges[1:]))

def ban_user(user_id, expiration_date=None, reason=None):
    """
    This function is used to ban a user. If the user is already banned, the
    function returns False. If the user is not already banned, this function
    bans the user using the arguments to build a new UserBan object.

    :returns    False if the user is already banned and the ban is not updated
    :returns    UserBan object if there is a new ban that was created.
    """
    user_ban =UserBan.query.filter(
            UserBan.user_id==user_id)
    if user_ban.count():
        return False
    new_user_ban = UserBan(
        user_id=user_id,
        expiration_date=expiration_date,
        reason=reason)
    return new_user_ban

def unban_user(user_id):
    """
    This function is used to unban a user. If the user is not currently banned,
    nothing happens.

    :returns    True if the operation was completed successfully and the user
                has been unbanned
    :returns    False if the user was never banned.
    """
    user_ban = UserBan.query.filter(
            UserBan.user_id==user_id)
    if user_ban.count() == 0:
        return False
    user_ban.first().delete()
    return True

def parse_report_panel_settings(form):
    """
    This function parses the url arguments to which are used to filter reports
    in the reports panel view. More filters can be added to make a usuable
    search function.

    :returns    A dictionary of sqlalchemy-usable filters.
    """
    filters = {}

    if form.validate():
        filters['reported_user_id'] = form.reported_user.data
        filters['reporter_id'] = form.reporter.data

    filters = dict((k, v)
        for k, v in six.iteritems(filters) if v)

    return filters
