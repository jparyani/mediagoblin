# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 MediaGoblin contributors.  See AUTHORS.
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

class TestingMiddleware(object):
    """
    Middleware for the Unit tests
    
    It might make sense to perform some tests on all
    requests/responses. Or prepare them in a special
    manner. For example all html responses could be tested
    for being valid html *after* being rendered.

    This module is getting inserted at the front of the
    middleware list, which means: requests are handed here
    first, responses last. So this wraps up the "normal"
    app.

    If you need to add a test, either add it directly to
    the appropiate process_request or process_response, or
    create a new method and call it from process_*.
    """

    def __init__(self, mg_app):
        self.app = mg_app

    def process_request(self, request):
        pass

    def process_response(self, request, response):
        # All following tests should be for html only!
        if response.content_type != "text/html":
            # Get out early
            return

        # If the template contains a reference to
        # /mgoblin_static/ instead of using
        # /request.staticdirect(), error out here.
        # This could probably be implemented as a grep on
        # the shipped templates easier...
        if response.text.find("/mgoblin_static/") >= 0:
            raise AssertionError(
                "Response HTML contains reference to /mgoblin_static/ "
                "instead of staticdirect. Request was for: "
                + request.full_path)

        return
