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

from werkzeug.exceptions import Forbidden

from mediagoblin.db.models import (MediaEntry, User, MediaComment, \
                                   CommentReport, ReportBase, Privilege, \
                                   UserBan, ArchivedReport)
from mediagoblin.db.util import user_privileges_to_dictionary
from mediagoblin.decorators import (require_admin_or_moderator_login, \
                                    active_user_from_url)
from mediagoblin.tools.response import render_to_response, redirect
from mediagoblin.moderation import forms as moderation_forms
from mediagoblin.moderation.tools import take_punitive_actions
from datetime import datetime

@require_admin_or_moderator_login
def moderation_media_processing_panel(request):
    '''
    Show the global media processing panel for this instance
    '''
    processing_entries = MediaEntry.query.filter_by(state = u'processing').\
        order_by(MediaEntry.created.desc())

    # Get media entries which have failed to process
    failed_entries = MediaEntry.query.filter_by(state = u'failed').\
        order_by(MediaEntry.created.desc())

    processed_entries = MediaEntry.query.filter_by(state = u'processed').\
        order_by(MediaEntry.created.desc()).limit(10)

    # Render to response
    return render_to_response(
        request,
        'mediagoblin/moderation/media_panel.html',
        {'processing_entries': processing_entries,
         'failed_entries': failed_entries,
         'processed_entries': processed_entries})

@require_admin_or_moderator_login
def moderation_users_panel(request):
    '''
    Show the global panel for monitoring users in this instance
    '''
    user_list = User.query

    return render_to_response(
        request,
        'mediagoblin/moderation/user_panel.html',
        {'user_list': user_list})

@require_admin_or_moderator_login
def moderation_users_detail(request):
    '''
    Shows details about a particular user.
    '''
    user = User.query.filter_by(username=request.matchdict['user']).first()
    active_reports = user.reports_filed_on.filter(
        ReportBase.discriminator!='archived_report').limit(5)
    closed_reports = user.reports_filed_on.filter(
        ReportBase.discriminator=='archived_report').all()
    privileges = Privilege.query
    user_banned = UserBan.query.get(user.id)
    user_privileges = user_privileges_to_dictionary(user.id)
    requesting_user_privileges = user_privileges_to_dictionary(request.user.id)

    return render_to_response(
        request,
        'mediagoblin/moderation/user.html',
        {'user':user,
         'privileges': privileges,
         'requesting_user_privileges':requesting_user_privileges,
         'reports':active_reports,
         'user_banned':user_banned})

@require_admin_or_moderator_login
def moderation_reports_panel(request):
    '''
    Show the global panel for monitoring reports filed against comments or 
        media entries for this instance.
    '''
    report_list = ReportBase.query.filter(
        ReportBase.discriminator!="archived_report").order_by(
        ReportBase.created.desc()).limit(10)
    closed_report_list = ReportBase.query.filter(
        ReportBase.discriminator=="archived_report").order_by(
        ReportBase.created.desc()).limit(10)

    # Render to response
    return render_to_response(
        request,
        'mediagoblin/moderation/report_panel.html',
        {'report_list':report_list,
         'closed_report_list':closed_report_list})

@require_admin_or_moderator_login
def moderation_reports_detail(request):
    """
    This is the page an admin or moderator goes to see the details of a report.
    The report can be resolved or unresolved. This is also the page that a mod-
    erator would go to to take an action to resolve a report.
    """
    form = moderation_forms.ReportResolutionForm(request.form)
    report = ReportBase.query.get(request.matchdict['report_id'])

    form.take_away_privileges.choices = [(s.privilege_name,s.privilege_name.title()) for s in report.reported_user.all_privileges]

    if request.method == "POST" and form.validate():
        user = User.query.get(form.targeted_user.data)
        return take_punitive_actions(request, form, report, user)


    form.targeted_user.data = report.reported_user_id

    return render_to_response(
        request,
        'mediagoblin/moderation/report.html',
        {'report':report,
         'form':form})

@require_admin_or_moderator_login
@active_user_from_url
def give_or_take_away_privilege(request, url_user):
    '''
    A form action to give or take away a particular privilege from a user
    '''
    form = moderation_forms.PrivilegeAddRemoveForm(request.form)
    if request.method == "POST" and form.validate():
        privilege = Privilege.one({'privilege_name':form.privilege_name.data})
        if privilege in url_user.all_privileges:
            url_user.all_privileges.remove(privilege)
        else:      
            url_user.all_privileges.append(privilege)
        url_user.save()
        return redirect(
            request,
            'mediagoblin.moderation.users_detail',
            user=url_user.username)
