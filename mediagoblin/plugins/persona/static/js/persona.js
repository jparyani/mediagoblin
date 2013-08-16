/**
 * GNU MediaGoblin -- federated, autonomous media hosting
 * Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

$(document).ready(function () {
    var signinLink = document.getElementById('persona_login');
    if (signinLink) {
        signinLink.onclick = function() { navigator.id.request(); };
    }

    var signinLink1 = document.getElementById('persona_login1');
    if (signinLink1) {
        signinLink1.onclick = function() { navigator.id.request(); };
    }

    var signoutLink = document.getElementById('logout');
    if (signoutLink) {
        signoutLink.onclick = function() { navigator.id.logout(); };
    }

    var logout_url = document.getElementById('_logout_url').value;

    navigator.id.watch({
        onlogin: function(assertion) {
            document.getElementById('_assertion').value = assertion;
            document.getElementById('_persona_login').submit()
    },
        onlogout: function() {
            $.ajax({
                type: 'GET',
                url: logout_url,
                success: function(res, status, xhr) { window.location.reload(); },
                error: function(xhr, status, err) { alert("Logout failure: " + err); }
            });
        }
    });
});
