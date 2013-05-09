# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2013 MediaGoblin contributors.  See AUTHORS.
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
from .tools import fixture_add_user


XML_PREFIX = "<?xml version='1.0' encoding='utf-8'?>\n"


class Test_PWG(object):
    @pytest.fixture(autouse=True)
    def setup(self, test_app):
        self.test_app = test_app

        fixture_add_user()

        self.username = u"chris"
        self.password = "toast"

    def do_post(self, method, params):
        params["method"] = method
        return self.test_app.post("/api/piwigo/ws.php", params)

    def do_get(self, method, params=None):
        if params is None:
            params = {}
        params["method"] = method
        return self.test_app.get("/api/piwigo/ws.php", params)

    def test_session(self):
        resp = self.do_post("pwg.session.login",
            {"username": u"nouser", "password": "wrong"})
        assert resp.body ==  XML_PREFIX + '<rsp stat="ok">0</rsp>'

        resp = self.do_post("pwg.session.login",
            {"username": self.username, "password": "wrong"})
        assert resp.body ==  XML_PREFIX + '<rsp stat="ok">0</rsp>'

        resp = self.do_get("pwg.session.getStatus")
        assert resp.body == XML_PREFIX \
            + '<rsp stat="ok"><username>guest</username></rsp>'

        resp = self.do_post("pwg.session.login",
            {"username": self.username, "password": self.password})
        assert resp.body ==  XML_PREFIX + '<rsp stat="ok">1</rsp>'

        resp = self.do_get("pwg.session.getStatus")
        assert resp.body == XML_PREFIX \
            + '<rsp stat="ok"><username>chris</username></rsp>'

        self.do_get("pwg.session.logout")

        resp = self.do_get("pwg.session.getStatus")
        assert resp.body == XML_PREFIX \
            + '<rsp stat="ok"><username>guest</username></rsp>'
