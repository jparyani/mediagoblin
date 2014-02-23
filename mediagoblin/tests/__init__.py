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

import pytest

from mediagoblin.db.models import User
from mediagoblin.tests.tools import fixture_add_user
from mediagoblin.tools import template


def setup_package():

    import warnings
    from sqlalchemy.exc import SAWarning
    warnings.simplefilter("error", SAWarning)


class MGClientTestCase:

    usernames = None

    @pytest.fixture(autouse=True)
    def setup(self, test_app):
        self.test_app = test_app

        if self.usernames is None:
            msg = ('The usernames attribute should be overridden '
                   'in the subclass')
            raise pytest.skip(msg)
        for username, options in self.usernames:
            fixture_add_user(username, **options)

    def user(self, username):
        return User.query.filter(User.username == username).first()

    def _do_request(self, url, *context_keys, **kwargs):
        template.clear_test_template_context()
        response = self.test_app.request(url, **kwargs)
        context_data = template.TEMPLATE_TEST_CONTEXT
        for key in context_keys:
            context_data = context_data[key]
        return response, context_data

    def do_get(self, url, *context_keys, **kwargs):
        kwargs['method'] = 'GET'
        return self._do_request(url, *context_keys, **kwargs)

    def do_post(self, url, *context_keys, **kwargs):
        kwargs['method'] = 'POST'
        return self._do_request(url, *context_keys, **kwargs)
