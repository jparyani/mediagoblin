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

import logging

from werkzeug.exceptions import MethodNotAllowed

from mediagoblin.meddleware.csrf import csrf_exempt
from mediagoblin.tools.response import render_404


_log = logging.getLogger(__name__)


class CmdTable(object):
    _cmd_table = {}

    def __init__(self, cmd_name, only_post=False):
        assert not cmd_name in self._cmd_table
        self.cmd_name = cmd_name
        self.only_post = only_post

    def __call__(self, to_be_wrapped):
        assert not self.cmd_name in self._cmd_table
        self._cmd_table[self.cmd_name] = (to_be_wrapped, self.only_post)
        return to_be_wrapped

    @classmethod
    def find_func(cls, request):
        if request.method == "GET":
            cmd_name = request.args.get("method")
        else:
            cmd_name = request.form.get("method")
        entry = cls._cmd_table.get(cmd_name)
        if not entry:
            return entry
        func, only_post = entry
        if only_post and request.method != "POST":
            _log.warn("Method %s only allowed for POST", cmd_name)
            raise MethodNotAllowed()
        return func
        

@CmdTable("pwg.session.login", True)
def pwg_login(request):
    username = request.form.get("username")
    password = request.form.get("password")
    _log.info("Login for %r/%r...", username, password)
    return render_404(request)


@csrf_exempt
def ws_php(request):
    if request.method not in ("GET", "POST"):
        _log.error("Method %r not supported", request.method)
        raise MethodNotAllowed()

    func = CmdTable.find_func(request)
    if not func:
        _log.warn("wsphp: Unhandled %s %r %r", request.method,
                  request.args, request.form)
        return render_404(request)

    result = func(request)

    return result
