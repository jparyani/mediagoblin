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


from mediagoblin.db.models import (MediaEntry, User,ReportBase, Privilege,
                                   UserBan)
from mediagoblin.decorators import (require_admin_or_moderator_login,
                                    active_user_from_url, user_has_privilege,
                                    allow_reporting)
from mediagoblin.tools.response import render_to_response, redirect
from mediagoblin.moderation import forms as moderation_forms
from mediagoblin.moderation.tools import (take_punitive_actions, \
    take_away_privileges, give_privileges, ban_user, unban_user, \
    parse_report_panel_settings)
from math import ceil

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
    current_page = 1
    if len(request.args) > 0:
        form = moderation_forms.UserPanelSortingForm(request.args)
        if form.validate():
            current_page = form.p.data or 1

    all_user_list = User.query
    user_list = all_user_list.order_by(
        User.created.desc()).offset(
            (current_page-1)*10).limit(10)
    last_page = int(ceil(all_user_list.count()/10.))

    return render_to_response(
        request,
        'mediagoblin/moderation/user_panel.html',
        {'user_list': user_list,
         'current_page':current_page,
         'last_page':last_page})

@require_admin_or_moderator_login
def moderation_users_detail(request):
    '''
    Shows details about a particular user.
    '''
    user = User.query.filter_by(username=request.matchdict['user']).first()
    active_reports = user.reports_filed_on.filter(
        ReportBase.resolved==None).limit(5)
    closed_reports = user.reports_filed_on.filter(
        ReportBase.resolved!=None).all()
    privileges = Privilege.query
    user_banned = UserBan.query.get(user.id)
    ban_form = moderation_forms.BanForm()

    return render_to_response(
        request,
        'mediagoblin/moderation/user.html',
        {'user':user,
         'privileges': privileges,
         'reports':active_reports,
         'user_banned':user_banned,
         'ban_form':ban_form})

@require_admin_or_moderator_login
@allow_reporting
def moderation_reports_panel(request):
    '''
    Show the global panel for monitoring reports filed against comments or
        media entries for this instance.
    '''
    filters = []
    active_settings, closed_settings = {'current_page':1}, {'current_page':1}

    if len(request.args) > 0:
        form = moderation_forms.ReportPanelSortingForm(request.args)
        if form.validate():
            filters = parse_report_panel_settings(form)
            active_settings['current_page'] = form.active_p.data or 1
            closed_settings['current_page'] = form.closed_p.data or 1
            filters = [
               getattr(ReportBase,key)==val
               for key,val in filters.viewitems()]

    all_active = ReportBase.query.filter(
        ReportBase.resolved==None).filter(
        *filters)
    all_closed = ReportBase.query.filter(
        ReportBase.resolved!=None).filter(
        *filters)

    # report_list and closed_report_list are the two lists of up to 10
    # items which are actually passed to the user in this request
    report_list = all_active.order_by(
        ReportBase.created.desc()).offset(
            (active_settings['current_page']-1)*10).limit(10)
    closed_report_list = all_closed.order_by(
        ReportBase.created.desc()).offset(
            (closed_settings['current_page']-1)*10).limit(10)

    active_settings['last_page'] = int(ceil(all_active.count()/10.))
    closed_settings['last_page'] = int(ceil(all_closed.count()/10.))
    # Render to response
    return render_to_response(
        request,
        'mediagoblin/moderation/report_panel.html',
        {'report_list':report_list,
         'closed_report_list':closed_report_list,
         'active_settings':active_settings,
         'closed_settings':closed_settings})

@require_admin_or_moderator_login
@allow_reporting
def moderation_reports_detail(request):
    """
    This is the page an admin or moderator goes to see the details of a report.
    The report can be resolved or unresolved. This is also the page that a mod-
    erator would go to to take an action to resolve a report.
    """
    form = moderation_forms.ReportResolutionForm(request.form)
    report = ReportBase.query.get(request.matchdict['report_id'])

    form.take_away_privileges.choices = [
        (s.privilege_name,s.privilege_name.title()) \
            for s in report.reported_user.all_privileges
    ]

    if request.method == "POST" and form.validate() and not (
        not request.user.has_privilege(u'admin') and
        report.reported_user.has_privilege(u'admin')):

        user = User.query.get(form.targeted_user.data)
        return take_punitive_actions(request, form, report, user)


    form.targeted_user.data = report.reported_user_id

    return render_to_response(
        request,
        'mediagoblin/moderation/report.html',
        {'report':report,
         'form':form})

@user_has_privilege(u'admin')
@active_user_from_url
def give_or_take_away_privilege(request, url_user):
    '''
    A form action to give or take away a particular privilege from a user.
    Can only be used by an admin.
    '''
    form = moderation_forms.PrivilegeAddRemoveForm(request.form)
    if request.method == "POST" and form.validate():
        privilege = Privilege.query.filter(
            Privilege.privilege_name==form.privilege_name.data).one()
        if not take_away_privileges(
            url_user.username, form.privilege_name.data):

            give_privileges(url_user.username, form.privilege_name.data)
        url_user.save()

    return redirect(
        request,
        'mediagoblin.moderation.users_detail',
        user=url_user.username)

@user_has_privilege(u'admin')
@active_user_from_url
def ban_or_unban(request, url_user):
    """
    A page to ban or unban a user. Only can be used by an admin.
    """
    form = moderation_forms.BanForm(request.form)
    if request.method == "POST" and form.validate():
        already_banned = unban_user(url_user.id)
        same_as_requesting_user = (request.user.id == url_user.id)
        if not already_banned and not same_as_requesting_user:
            user_ban = ban_user(url_user.id,
                expiration_date = form.user_banned_until.data,
                reason = form.why_user_was_banned.data)
            user_ban.save()
    return redirect(
        request,
        'mediagoblin.moderation.users_detail',
        user=url_user.username)
