# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 Free Software Foundation, Inc
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

from routes.route import Route

auth_routes = [
    Route('mediagoblin.auth.register', '/register/',
          controller='mediagoblin.auth.views:register'),
    Route('mediagoblin.auth.register_success', '/register/success/',
          controller='mediagoblin.auth.views:register_success'),
    Route('mediagoblin.auth.login', '/login/',
          controller='mediagoblin.auth.views:login'),
    Route('mediagoblin.auth.logout', '/logout/',
          controller='mediagoblin.auth.views:logout'),
    Route('mediagoblin.auth.verify_email', '/verify_email/',
          controller='mediagoblin.auth.views:verify_email'),
    Route('mediagoblin.auth.verify_email_notice', '/verification_required/',
          controller='mediagoblin.auth.views:verify_email_notice'),
    Route('mediagoblin.auth.resend_verification', '/resend_verification/',
          controller='mediagoblin.auth.views:resend_activation'),
    Route('mediagoblin.auth.resend_verification_success',
          '/resend_verification_success/',
          controller='mediagoblin.auth.views:resend_activation_success')]
