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

from mediagoblin import mg_globals
from mediagoblin.db.models import User, Privilege, ArchivedReport, UserBan
from mediagoblin.db.base import Session
from mediagoblin.tools.mail import send_email
from mediagoblin.tools.response import redirect
from datetime import datetime
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _
import sys, traceback

def take_punitive_actions(request, form, report, user):
    message_body =''
    try:

        # The bulk of this action is running through all of the different
        # punitive actions that a moderator could take.
        if u'takeaway' in form.action_to_resolve.data:
            for privilege_name in form.take_away_privileges.data:
                take_away_privileges(user.username, privilege_name)
                form.resolution_content.data += \
                    u"<br>%s took away %s\'s %s privileges." % (
                        request.user.username,
                        user.username,
                        privilege_name)

        # If the moderator elects to ban the user, a new instance of user_ban
        # will be created.
        if u'userban' in form.action_to_resolve.data:
            reason = form.resolution_content.data + \
                "<br>"+request.user.username
            user_ban = UserBan(
                user_id=form.targeted_user.data,
                expiration_date=form.user_banned_until.data,
                reason= form.why_user_was_banned.data
            )
            Session.add(user_ban)

            if form.user_banned_until.data is not None:
                form.resolution_content.data += \
                    u"<br>%s banned user %s until %s." % (
                    request.user.username,
                    user.username,
                    form.user_banned_until.data)
            else:
                form.resolution_content.data += \
                    u"<br>%s banned user %s indefinitely." % (
                    request.user.username,
                    user.username)

        # If the moderator elects to send a warning message. An email will be
        # sent to the email address given at sign up
        if u'sendmessage' in form.action_to_resolve.data:
            message_body = form.message_to_user.data
            form.resolution_content.data += \
                u"<br>%s sent a warning email to the offender." % (
                    request.user.username)

        archive = ArchivedReport(
            reporter_id=report.reporter_id,
            report_content=report.report_content,
            reported_user_id=report.reported_user_id,
            created=report.created,
            resolved=datetime.now(),
            resolver_id=request.user.id
            )

        if u'delete' in form.action_to_resolve.data and \
            report.is_comment_report():
                deleted_comment = report.comment
                Session.delete(deleted_comment)
                form.resolution_content.data += \
                    u"<br>%s deleted the comment." % (
                        request.user.username)
        elif u'delete' in form.action_to_resolve.data and \
            report.is_media_entry_report():
                deleted_media = report.media_entry
                Session.delete(deleted_media)
                form.resolution_content.data += \
                    u"<br>%s deleted the media entry." % (
                        request.user.username)

        # If the moderator didn't delete the content we then attach the
        # content to the archived report. We also have to actively delete the
        # old report, since it won't be deleted by cascading.
        elif report.is_comment_report():
            archive.comment_id = report.comment_id
            Session.delete(report)
        elif report.is_media_entry_report():
            archive.media_entry_id = report.media_entry.id
            Session.delete(report)


        archive.result=form.resolution_content.data
        Session.add(archive)
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
    except:
#TODO make a more effective and specific try except statement. To account for
# incorrect value addition my moderators
        print sys.exc_info()[0]
        print sys.exc_info()[1]
        traceback.print_tb(sys.exc_info()[2])
        Session.rollback()
        return redirect(
            request,
            'mediagoblin.moderation.reports_detail',
            report_id=report.id)

def take_away_privileges(user,*privileges):
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

