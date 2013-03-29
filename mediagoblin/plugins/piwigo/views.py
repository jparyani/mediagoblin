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
import re

from werkzeug.exceptions import MethodNotAllowed, BadRequest, NotImplemented
from werkzeug.wrappers import BaseResponse

from mediagoblin import mg_globals
from mediagoblin.meddleware.csrf import csrf_exempt
from mediagoblin.submit.lib import check_file_field
from .tools import CmdTable, PwgNamedArray, response_xml
from .forms import AddSimpleForm


_log = logging.getLogger(__name__)


@CmdTable("pwg.session.login", True)
def pwg_login(request):
    username = request.form.get("username")
    password = request.form.get("password")
    _log.info("Login for %r/%r...", username, password)
    return True


@CmdTable("pwg.session.logout")
def pwg_logout(request):
    _log.info("Logout")
    return True


@CmdTable("pwg.getVersion")
def pwg_getversion(request):
    return "2.5.0 (MediaGoblin)"


@CmdTable("pwg.session.getStatus")
def pwg_session_getStatus(request):
    return {'username': "fake_user"}


@CmdTable("pwg.categories.getList")
def pwg_categories_getList(request):
    catlist = ({'id': -29711,
                'uppercats': "-29711",
                'name': "All my images"},)
    return {
          'categories': PwgNamedArray(
            catlist,
            'category',
            (
              'id',
              'url',
              'nb_images',
              'total_nb_images',
              'nb_categories',
              'date_last',
              'max_date_last',
            )
          )
        }


@CmdTable("pwg.images.exist")
def pwg_images_exist(request):
    return {}


@CmdTable("pwg.images.addSimple", True)
def pwg_images_addSimple(request):
    form = AddSimpleForm(request.form)
    if not form.validate():
        _log.error("addSimple: form failed")
        raise BadRequest()
    dump = []
    for f in form:
        dump.append("%s=%r" % (f.name, f.data))
    _log.info("addimple: %r %s %r", request.form, " ".join(dump), request.files)

    if not check_file_field(request, 'image'):
        raise BadRequest()

    return {'image_id': 123456, 'url': ''}

                
md5sum_matcher = re.compile(r"^[0-9a-fA-F]{32}$")

def fetch_md5(request, parm_name, optional_parm=False):
    val = request.form.get(parm_name)
    if (val is None) and (not optional_parm):
        _log.error("Parameter %s missing", parm_name)
        raise BadRequest("Parameter %s missing" % parm_name)
    if not md5sum_matcher.match(val):
        _log.error("Parameter %s=%r has no valid md5 value", parm_name, val)
        raise BadRequest("Parameter %s is not md5" % parm_name)
    return val


@CmdTable("pwg.images.addChunk", True)
def pwg_images_addChunk(request):
    o_sum = fetch_md5(request, 'original_sum')
    typ = request.form.get('type')
    pos = request.form.get('position')
    data = request.form.get('data')

    # Validate params:
    pos = int(pos)
    if not typ in ("file", "thumb"):
        _log.error("type %r not allowed for now", typ)
        return False

    _log.info("addChunk for %r, type %r, position %d, len: %d",
              o_sum, typ, pos, len(data))
    if typ == "thumb":
        _log.info("addChunk: Ignoring thumb, because we create our own")
        return True

    return True


def possibly_add_cookie(request, response):
    # TODO: We should only add a *real* cookie, if
    # authenticated. And if there is no cookie already.
    if True:
        response.set_cookie(
            'pwg_id',
            "some_fake_for_now",
            path=request.environ['SCRIPT_NAME'],
            domain=mg_globals.app_config.get('csrf_cookie_domain'),
            secure=(request.scheme.lower() == 'https'),
            httponly=True)


@csrf_exempt
def ws_php(request):
    if request.method not in ("GET", "POST"):
        _log.error("Method %r not supported", request.method)
        raise MethodNotAllowed()

    func = CmdTable.find_func(request)
    if not func:
        _log.warn("wsphp: Unhandled %s %r %r", request.method,
                  request.args, request.form)
        raise NotImplemented()

    result = func(request)

    if isinstance(result, BaseResponse):
        return result

    response = response_xml(result)

    possibly_add_cookie(request, response)

    return response
