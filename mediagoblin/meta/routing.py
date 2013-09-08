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

meta_routes = [
    ('mediagoblin.meta.terms_of_service',
        '/tos/',
        'mediagoblin.meta.views:terms_of_service'),
    ('mediagoblin.meta.reports_panel',
        '/reports/',
        'mediagoblin.meta.views:public_reports_panel'),
    ('mediagoblin.meta.reports_detail',
        '/reports/<int:report_id>',
        'mediagoblin.meta.views:public_reports_details')
]
