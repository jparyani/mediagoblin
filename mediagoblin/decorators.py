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


from bson.errors import InvalidId
from webob import exc

from mediagoblin.db.util import ObjectId


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
            return exc.HTTPFound(
                location = request.urlgen(
                    'mediagoblin.auth.verify_email_notice'))
        elif not request.user or request.user.get('status') != u'active':
            return exc.HTTPFound(
                location="%s?next=%s" % (
                    request.urlgen("mediagoblin.auth.login"),
                    request.path_info))

        return controller(request, *args, **kwargs)

    return _make_safe(new_controller_func, controller)


def uses_pagination(controller):
    """
    Check request GET 'page' key for wrong values
    """
    def wrapper(request, *args, **kwargs):
        try:
            page = int(request.GET.get('page', 1))
            if page < 0:
                return exc.HTTPNotFound()
        except ValueError:
            return exc.HTTPNotFound()

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
            return exc.HTTPNotFound()

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
                return exc.HTTPNotFound()

            # Still no media?  Okay, 404.
            if not media:
                return exc.HTTPNotFound()

        return controller(request, media=media, *args, **kwargs)

    return _make_safe(wrapper, controller)
