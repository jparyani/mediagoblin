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
from os.path import splitext
import shutil

from werkzeug.exceptions import MethodNotAllowed, BadRequest, NotImplemented
from werkzeug.wrappers import BaseResponse

from mediagoblin.meddleware.csrf import csrf_exempt
from mediagoblin.auth.lib import fake_login_attempt
from mediagoblin.media_types import sniff_media
from mediagoblin.submit.lib import check_file_field, prepare_queue_task, \
    run_process_media

from .tools import CmdTable, response_xml, check_form, \
    PWGSession, PwgNamedArray, PwgError
from .forms import AddSimpleForm, AddForm


_log = logging.getLogger(__name__)


@CmdTable("pwg.session.login", True)
def pwg_login(request):
    username = request.form.get("username")
    password = request.form.get("password")
    user = request.db.User.query.filter_by(username=username).first()
    if not user:
        _log.info("User %r not found", username)
        fake_login_attempt()
        return PwgError(999, 'Invalid username/password')
    if not user.check_login(password):
        _log.warn("Wrong password for %r", username)
        return PwgError(999, 'Invalid username/password')
    _log.info("Logging %r in", username)
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

    filename = request.files['image'].filename

    # Sniff the submitted media to determine which
    # media plugin should handle processing
    media_type, media_manager = sniff_media(
        request.files['image'])

    # create entry and save in database
    entry = request.db.MediaEntry()
    entry.media_type = unicode(media_type)
    entry.title = (
        unicode(form.name.data)
        or unicode(splitext(filename)[0]))

    entry.description = unicode(form.comment.data)

    # entry.license = unicode(form.license.data) or None

    entry.uploader = request.user.id

    '''
    # Process the user's folksonomy "tags"
    entry.tags = convert_to_tag_list_of_dicts(
        form.tags.data)
    '''

    # Generate a slug from the title
    entry.generate_slug()

    queue_file = prepare_queue_task(request.app, entry, filename)

    with queue_file:
        shutil.copyfileobj(request.files['image'].stream,
                           queue_file,
                           length=4 * 1048576)

    # Save now so we have this data before kicking off processing
    entry.save()

    # Pass off to processing
    #
    # (... don't change entry after this point to avoid race
    # conditions with changes to the document via processing code)
    feed_url = request.urlgen(
        'mediagoblin.user_pages.atom_feed',
        qualified=True, user=request.user.username)
    run_process_media(entry, feed_url)

    return {'image_id': entry.id, 'url': entry.url_for_self(request.urlgen,
                                                            qualified=True)}


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
