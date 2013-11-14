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

from mediagoblin.tools.translate import pass_to_ugettext as _
from mediagoblin.meddleware.csrf import csrf_exempt
from mediagoblin.auth.tools import check_login_simple
from mediagoblin.submit.lib import \
    submit_media, check_file_field, get_upload_file_limits, \
    FileUploadLimit, UserUploadLimit, UserPastUploadLimit


from mediagoblin.user_pages.lib import add_media_to_collection
from mediagoblin.db.models import Collection

from .tools import CmdTable, response_xml, check_form, \
    PWGSession, PwgNamedArray, PwgError
from .forms import AddSimpleForm, AddForm


_log = logging.getLogger(__name__)


@CmdTable("pwg.session.login", True)
def pwg_login(request):
    username = request.form.get("username")
    password = request.form.get("password")
    user = check_login_simple(username, password)
    if not user:
        return PwgError(999, 'Invalid username/password')
    request.session["user_id"] = user.id
    request.session.save()
    return True


@CmdTable("pwg.session.logout")
def pwg_logout(request):
    _log.info("Logout")
    request.session.delete()
    return True


@CmdTable("pwg.getVersion")
def pwg_getversion(request):
    return "2.5.0 (MediaGoblin)"


@CmdTable("pwg.session.getStatus")
def pwg_session_getStatus(request):
    if request.user:
        username = request.user.username
    else:
        username = "guest"
    return {'username': username}


@CmdTable("pwg.categories.getList")
def pwg_categories_getList(request):
    catlist = [{'id': -29711,
                'uppercats': "-29711",
                'name': "All my images"}]

    if request.user:
        collections = Collection.query.filter_by(
            get_creator=request.user).order_by(Collection.title)

        for c in collections:
            catlist.append({'id': c.id,
                            'uppercats': str(c.id),
                            'name': c.title,
                            'comment': c.description
                            })

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
    _log.info("addSimple: %r %s %r", request.form, " ".join(dump),
              request.files)

    if not check_file_field(request, 'image'):
        raise BadRequest()

    upload_limit, max_file_size = get_upload_file_limits(request.user)

    try:
        entry = submit_media(
            mg_app=request.app, user=request.user,
            submitted_file=request.files['image'],
            filename=request.files['image'].filename,
            title=unicode(form.name.data),
            description=unicode(form.comment.data),
            upload_limit=upload_limit, max_file_size=max_file_size)

        collection_id = form.category.data
        if collection_id > 0:
            collection = Collection.query.get(collection_id)
            if collection is not None and collection.creator == request.user.id:
                add_media_to_collection(collection, entry, "")

        return {
            'image_id': entry.id,
            'url': entry.url_for_self(
                request.urlgen,
                qualified=True)}

    # Handle upload limit issues
    except FileUploadLimit:
        raise BadRequest(
            _(u'Sorry, the file size is too big.'))
    except UserUploadLimit:
        raise BadRequest(
            _('Sorry, uploading this file will put you over your'
              ' upload limit.'))
    except UserPastUploadLimit:
        raise BadRequest(
            _('Sorry, you have reached your upload limit.'))


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


@CmdTable("pwg.images.add", True)
def pwg_images_add(request):
    _log.info("add: %r", request.form)
    form = AddForm(request.form)
    check_form(form)

    return {'image_id': 123456, 'url': ''}


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

    with PWGSession(request) as session:
        result = func(request)

        if isinstance(result, BaseResponse):
            return result

        response = response_xml(result)
        session.save_to_cookie(response)

        return response
