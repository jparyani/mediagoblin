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

from mediagoblin.tools.response import render_to_response


def code_of_conduct(request):
    return render_to_response(request,
        'mediagoblin/meta/code_of_conduct.html',
        {})

def public_reports_panel(request):
    return render_to_response(request,
        'mediagoblin/meta/reports_panel.html',
        {})

def public_reports_details(request):
    return render_to_response(request,
        'mediagoblin/meta/reports_details.html',
        {})
