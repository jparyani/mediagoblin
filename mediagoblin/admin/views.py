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

from mediagoblin.db.models import MediaEntry, User, MediaComment, CommentReport, ReportBase
from mediagoblin.decorators import require_admin_login
from mediagoblin.tools.response import render_to_response

@require_admin_login
def admin_processing_panel(request):
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
        'mediagoblin/admin/panel.html',
        {'processing_entries': processing_entries,
         'failed_entries': failed_entries,
         'processed_entries': processed_entries})

@require_admin_login
def admin_users_panel(request):
    '''
    Show the global panel for monitoring users in this instance
    '''
    user_list = User.query

    # Render to response
    return render_to_response(
        request,
        'mediagoblin/admin/user.html',
        {'user_list': user_list})

@require_admin_login
def admin_reports_panel(request):
    '''
    Show the global panel for monitoring reports filed against comments or 
        media entries for this instance.
    '''
    report_list = ReportBase.query.filter(
        ReportBase.resolved==None).order_by(
        ReportBase.created.desc()).limit(10)
    closed_report_list = ReportBase.query.filter(
        ReportBase.resolved!=None).order_by(
        ReportBase.created.desc()).limit(10)

    # Render to response
    return render_to_response(
        request,
        'mediagoblin/admin/report.html',
        {'report_list':report_list,
         'closed_report_list':closed_report_list})

