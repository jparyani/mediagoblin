# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 Free Software Foundation, Inc
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


from webob import exc

from mediagoblin.util import redirect, render_404
from mediagoblin.db.util import ObjectId, InvalidId


def _make_safe(decorator, original):
    """
    Copy the function data from the old function to the decorator.
    """
    decorator.__name__ = original.__name__
    decorator.__dict__ = original.__dict__
    decorator.__doc__ = original.__doc__
    return decorator


def require_active_login(controller):
    """
    Require an active login from the user.
    """
    def new_controller_func(request, *args, **kwargs):
        if request.user and \
                request.user.get('status') == u'needs_email_verification':
            return redirect(
                request, 'mediagoblin.user_pages.user_home',
                user=request.user['username'])
        elif not request.user or request.user.get('status') != u'active':
            return exc.HTTPFound(
                location="%s?next=%s" % (
                    request.urlgen("mediagoblin.auth.login"),
                    request.path_info))

        return controller(request, *args, **kwargs)

    return _make_safe(new_controller_func, controller)


def user_may_delete_media(controller):
    """
    Require user ownership of the MediaEntry to delete.
    """
    def wrapper(request, *args, **kwargs):
        uploader = request.db.MediaEntry.find_one(
            {'_id': ObjectId(request.matchdict['media'])}).uploader()
        if not (request.user['is_admin'] or
                request.user['_id'] == uploader['_id']):
            return exc.HTTPForbidden()

        return controller(request, *args, **kwargs)

    return _make_safe(wrapper, controller)


def uses_pagination(controller):
    """
    Check request GET 'page' key for wrong values
    """
    def wrapper(request, *args, **kwargs):
        try:
            page = int(request.GET.get('page', 1))
            if page < 0:
                return render_404(request)
        except ValueError:
            return render_404(request)

        return controller(request, page=page, *args, **kwargs)

    return _make_safe(wrapper, controller)


def get_user_media_entry(controller):
    """
    Pass in a MediaEntry based off of a url component
    """
    def wrapper(request, *args, **kwargs):
        user = request.db.User.find_one(
            {'username': request.matchdict['user']})

        if not user:
            return render_404(request)

        media = request.db.MediaEntry.find_one(
            {'slug': request.matchdict['media'],
             'state': 'processed',
             'uploader': user['_id']})

        # no media via slug?  Grab it via ObjectId
        if not media:
            try:
                media = request.db.MediaEntry.find_one(
                    {'_id': ObjectId(request.matchdict['media']),
                     'state': 'processed',
                     'uploader': user['_id']})
            except InvalidId:
                return render_404(request)

            # Still no media?  Okay, 404.
            if not media:
                return render_404(request)

        return controller(request, media=media, *args, **kwargs)

    return _make_safe(wrapper, controller)

def get_media_entry_by_id(controller):
    """
    Pass in a MediaEntry based off of a url component
    """
    def wrapper(request, *args, **kwargs):
        try:
            media = request.db.MediaEntry.find_one(
                {'_id': ObjectId(request.matchdict['media']),
                 'state': 'processed'})
        except InvalidId:
            return render_404(request)

        # Still no media?  Okay, 404.
        if not media:
            return render_404(request)

        return controller(request, media=media, *args, **kwargs)

    return _make_safe(wrapper, controller)

