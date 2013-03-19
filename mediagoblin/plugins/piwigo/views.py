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

import lxml.etree as ET
from werkzeug.exceptions import MethodNotAllowed

from mediagoblin.meddleware.csrf import csrf_exempt
from mediagoblin.tools.response import Response, render_404


_log = logging.getLogger(__name__)


def _fill_element_dict(el, data, as_attr=()):
    for k,v in data.iteritems():
        if k in as_attr:
            el.set(k, v)
        else:
            n = ET.SubElement(el, k)
            _fill_element(n, v)


def _fill_element(el, data):
    if isinstance(data, bool):
        if data:
            el.text = "1"
        else:
            el.text = "0"
    elif isinstance(data, basestring):
        el.text = data
    elif isinstance(data, dict):
        _fill_element_dict(el, data)
    else:
        _log.warn("Can't convert to xml: %r", data)


def as_xml(result):
    r = ET.Element("rsp")
    r.set("stat", "ok")
    _fill_element(r, result)
    return Response(ET.tostring(r, encoding="utf-8", xml_declaration=True),
                    content_type='text/xml')


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
        

@CmdTable("gmg.test")
def gmg_test(request):
    _log.info("Test...")
    r = {"abc": "def", "subdict": {"name": "Foo", "True": True}}
    return as_xml(r)


@CmdTable("pwg.session.login", True)
def pwg_login(request):
    username = request.form.get("username")
    password = request.form.get("password")
    _log.info("Login for %r/%r...", username, password)
    _log.warn("login: %s %r %r", request.method,
                  request.args, request.form)
    return as_xml(True)


@CmdTable("pwg.session.logout")
def pwg_logout(request):
    _log.info("Logout")
    return as_xml(True)


@CmdTable("pwg.getVersion")
def pwg_getversion(request):
    _log.info("getversion")
    return as_xml("piwigo 2.5.0")


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
