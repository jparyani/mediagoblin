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


auth_routes = [
    ('mediagoblin.auth.register', '/register/',
     'mediagoblin.auth.views:register'),
    ('mediagoblin.auth.login', '/login/',
     'mediagoblin.auth.views:login'),
    ('mediagoblin.auth.logout', '/logout/',
     'mediagoblin.auth.views:logout'),
    ('mediagoblin.auth.verify_email', '/verify_email/',
     'mediagoblin.auth.views:verify_email'),
    ('mediagoblin.auth.resend_verification', '/resend_verification/',
     'mediagoblin.auth.views:resend_activation'),
    ('mediagoblin.auth.forgot_password', '/forgot_password/',
     'mediagoblin.auth.views:forgot_password'),
    ('mediagoblin.auth.verify_forgot_password',
     '/forgot_password/verify/',
     'mediagoblin.auth.views:verify_forgot_password')]
