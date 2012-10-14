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

from routes.route import add_route
from mediagoblin.routing import add_route

add_route('mediagoblin.auth.logout',
          '/auth/logout/', 'mediagoblin.auth.views:logout')


add_route('mediagoblin.auth.register', '/register/',
        'mediagoblin.auth.views:register')

add_route('mediagoblin.auth.login', '/login/',
        'mediagoblin.auth.views:login')

add_route('mediagoblin.auth.logout', '/logout/',
        'mediagoblin.auth.views:logout')

add_route('mediagoblin.auth.verify_email', '/verify_email/',
        'mediagoblin.auth.views:verify_email')

add_route('mediagoblin.auth.resend_verification', '/resend_verification/',
        'mediagoblin.auth.views:resend_activation')

add_route('mediagoblin.auth.resend_verification_success',
        '/resend_verification_success/',
        template='mediagoblin/auth/resent_verification_email.html',
        'mediagoblin.views:simple_template_render')

add_route('mediagoblin.auth.forgot_password', '/forgot_password/',
        'mediagoblin.auth.views:forgot_password')

add_route('mediagoblin.auth.verify_forgot_password',
        '/forgot_password/verify/',
        'mediagoblin.auth.views:verify_forgot_password')
