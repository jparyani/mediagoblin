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

from collections import namedtuple
import logging

import six
import lxml.etree as ET
from werkzeug.exceptions import MethodNotAllowed, BadRequest

from mediagoblin.tools.request import setup_user_in_request
from mediagoblin.tools.response import Response


_log = logging.getLogger(__name__)


PwgError = namedtuple("PwgError", ["code", "msg"])


class PwgNamedArray(list):
    def __init__(self, l, item_name, as_attrib=()):
        self.item_name = item_name
        self.as_attrib = as_attrib
        list.__init__(self, l)

    def fill_element_xml(self, el):
        for it in self:
            n = ET.SubElement(el, self.item_name)
            if isinstance(it, dict):
                _fill_element_dict(n, it, self.as_attrib)
            else:
                _fill_element(n, it)


def _fill_element_dict(el, data, as_attr=()):
    for k, v in data.iteritems():
        if k in as_attr:
            if not isinstance(v, six.string_types):
                v = str(v)
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
    elif isinstance(data, six.string_types):
        el.text = data
    elif isinstance(data, int):
        el.text = str(data)
    elif isinstance(data, dict):
        _fill_element_dict(el, data)
    elif isinstance(data, PwgNamedArray):
        data.fill_element_xml(el)
    else:
        _log.warn("Can't convert to xml: %r", data)


def response_xml(result):
    r = ET.Element("rsp")
    r.set("stat", "ok")
    status = None
    if isinstance(result, PwgError):
        r.set("stat", "fail")
        err = ET.SubElement(r, "err")
        err.set("code", str(result.code))
        err.set("msg", result.msg)
        if result.code >= 100 and result.code < 600:
            status = result.code
    else:
        _fill_element(r, result)
    return Response(ET.tostring(r, encoding="utf-8", xml_declaration=True),
                    mimetype='text/xml', status=status)


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
        _log.debug("Found method %s", cmd_name)
        func, only_post = entry
        if only_post and request.method != "POST":
            _log.warn("Method %s only allowed for POST", cmd_name)
            raise MethodNotAllowed()
        return func


def check_form(form):
    if not form.validate():
        _log.error("form validation failed for form %r", form)
        for f in form:
            if len(f.errors):
                _log.error("Errors for %s: %r", f.name, f.errors)
        raise BadRequest()
    dump = []
    for f in form:
        dump.append("%s=%r" % (f.name, f.data))
    _log.debug("form: %s", " ".join(dump))


class PWGSession(object):
    session_manager = None

    def __init__(self, request):
        self.request = request
        self.in_pwg_session = False

    def __enter__(self):
        # Backup old state
        self.old_session = self.request.session
        self.old_user = self.request.user
        # Load piwigo session into state
        self.request.session = self.session_manager.load_session_from_cookie(
            self.request)
        setup_user_in_request(self.request)
        self.in_pwg_session = True
        return self

    def __exit__(self, *args):
        # Restore state
        self.request.session = self.old_session
        self.request.user = self.old_user
        self.in_pwg_session = False

    def save_to_cookie(self, response):
        assert self.in_pwg_session
        self.session_manager.save_session_to_cookie(self.request.session,
            self.request, response)
