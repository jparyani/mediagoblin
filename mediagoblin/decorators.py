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
        if not request.user or not request.user.get('status') == u'active':
            # TODO: Indicate to the user that they were redirected
            # here because an *active* user is required.
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

        return controller(request, page, *args, **kwargs)    

    return _make_safe(wrapper,controller)
