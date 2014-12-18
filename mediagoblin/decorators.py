# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
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

from functools import wraps

from werkzeug.exceptions import Forbidden, NotFound
from oauthlib.oauth1 import ResourceEndpoint

from six.moves.urllib.parse import urljoin

from mediagoblin import mg_globals as mgg
from mediagoblin import messages
from mediagoblin.db.models import MediaEntry, User, MediaComment, AccessToken
from mediagoblin.tools.response import (
    redirect, render_404,
    render_user_banned, json_response)
from mediagoblin.tools.translate import pass_to_ugettext as _

from mediagoblin.oauth.tools.request import decode_authorization_header
from mediagoblin.oauth.oauth import GMGRequestValidator


def user_not_banned(controller):
    """
    Requires that the user has not been banned. Otherwise redirects to the page
    explaining why they have been banned
    """
    @wraps(controller)
    def wrapper(request, *args, **kwargs):
        if request.user:
            if request.user.is_banned():
                return render_user_banned(request)
        return controller(request, *args, **kwargs)

    return wrapper


def require_active_login(controller):
    """
    Require an active login from the user. If the user is banned, redirects to
    the "You are Banned" page.
    """
    @wraps(controller)
    @user_not_banned
    def new_controller_func(request, *args, **kwargs):
        if request.user and \
                not request.user.has_privilege(u'active'):
            return redirect(
                request, 'mediagoblin.user_pages.user_home',
                user=request.user.username)
        elif not request.user or not request.user.has_privilege(u'active'):
            next_url = urljoin(
                    request.urlgen('mediagoblin.auth.login',
                        qualified=True),
                    request.url)

            return redirect(request, 'mediagoblin.auth.login',
                            next=next_url)

        return controller(request, *args, **kwargs)

    return new_controller_func


def user_has_privilege(privilege_name, allow_admin=True):
    """
    Requires that a user have a particular privilege in order to access a page.
    In order to require that a user have multiple privileges, use this
    decorator twice on the same view. This decorator also makes sure that the
    user is not banned, or else it redirects them to the "You are Banned" page.

        :param privilege_name       A unicode object that is that represents
                                        the privilege object. This object is
                                        the name of the privilege, as assigned
                                        in the Privilege.privilege_name column

        :param allow_admin          If this is true then if the user is an admin
                                    it will allow the user even if the user doesn't
                                    have the privilage given in privilage_name.
    """

    def user_has_privilege_decorator(controller):
        @wraps(controller)
        @require_active_login
        def wrapper(request, *args, **kwargs):
            if not request.user.has_privilege(privilege_name, allow_admin):
                raise Forbidden()

            return controller(request, *args, **kwargs)

        return wrapper
    return user_has_privilege_decorator


def active_user_from_url(controller):
    """Retrieve User() from <user> URL pattern and pass in as url_user=...

    Returns a 404 if no such active user has been found"""
    @wraps(controller)
    def wrapper(request, *args, **kwargs):
        user = User.query.filter_by(username=request.matchdict['user']).first()
        if user is None:
            return render_404(request)

        return controller(request, *args, url_user=user, **kwargs)

    return wrapper


def user_may_delete_media(controller):
    """
    Require user ownership of the MediaEntry to delete.
    """
    @wraps(controller)
    def wrapper(request, *args, **kwargs):
        uploader_id = kwargs['media'].uploader
        if not (request.user.has_privilege(u'admin') or
                request.user.id == uploader_id):
            raise Forbidden()

        return controller(request, *args, **kwargs)

    return wrapper


def user_may_alter_collection(controller):
    """
    Require user ownership of the Collection to modify.
    """
    @wraps(controller)
    def wrapper(request, *args, **kwargs):
        creator_id = request.db.User.query.filter_by(
            username=request.matchdict['user']).first().id
        if not (request.user.has_privilege(u'admin') or
                request.user.id == creator_id):
            raise Forbidden()

        return controller(request, *args, **kwargs)

    return wrapper


def uses_pagination(controller):
    """
    Check request GET 'page' key for wrong values
    """
    @wraps(controller)
    def wrapper(request, *args, **kwargs):
        try:
            page = int(request.GET.get('page', 1))
            if page < 0:
                return render_404(request)
        except ValueError:
            return render_404(request)

        return controller(request, page=page, *args, **kwargs)

    return wrapper


def get_user_media_entry(controller):
    """
    Pass in a MediaEntry based off of a url component
    """
    @wraps(controller)
    def wrapper(request, *args, **kwargs):
        user = User.query.filter_by(username=request.matchdict['user']).first()
        if not user:
            raise NotFound()

        media = None

        # might not be a slug, might be an id, but whatever
        media_slug = request.matchdict['media']

        # if it starts with id: it actually isn't a slug, it's an id.
        if media_slug.startswith(u'id:'):
            try:
                media = MediaEntry.query.filter_by(
                    id=int(media_slug[3:]),
                    state=u'processed',
                    uploader=user.id).first()
            except ValueError:
                raise NotFound()
        else:
            # no magical id: stuff?  It's a slug!
            media = MediaEntry.query.filter_by(
                slug=media_slug,
                state=u'processed',
                uploader=user.id).first()

        if not media:
            # Didn't find anything?  Okay, 404.
            raise NotFound()

        return controller(request, media=media, *args, **kwargs)

    return wrapper


def get_user_collection(controller):
    """
    Pass in a Collection based off of a url component
    """
    @wraps(controller)
    def wrapper(request, *args, **kwargs):
        user = request.db.User.query.filter_by(
            username=request.matchdict['user']).first()

        if not user:
            return render_404(request)

        collection = request.db.Collection.query.filter_by(
            slug=request.matchdict['collection'],
            creator=user.id).first()

        # Still no collection?  Okay, 404.
        if not collection:
            return render_404(request)

        return controller(request, collection=collection, *args, **kwargs)

    return wrapper


def get_user_collection_item(controller):
    """
    Pass in a CollectionItem based off of a url component
    """
    @wraps(controller)
    def wrapper(request, *args, **kwargs):
        user = request.db.User.query.filter_by(
            username=request.matchdict['user']).first()

        if not user:
            return render_404(request)

        collection_item = request.db.CollectionItem.query.filter_by(
            id=request.matchdict['collection_item']).first()

        # Still no collection item?  Okay, 404.
        if not collection_item:
            return render_404(request)

        return controller(request, collection_item=collection_item, *args, **kwargs)

    return wrapper


def get_media_entry_by_id(controller):
    """
    Pass in a MediaEntry based off of a url component
    """
    @wraps(controller)
    def wrapper(request, *args, **kwargs):
        media = MediaEntry.query.filter_by(
                id=request.matchdict['media_id'],
                state=u'processed').first()
        # Still no media?  Okay, 404.
        if not media:
            return render_404(request)

        given_username = request.matchdict.get('user')
        if given_username and (given_username != media.get_uploader.username):
            return render_404(request)

        return controller(request, media=media, *args, **kwargs)

    return wrapper


def get_workbench(func):
    """Decorator, passing in a workbench as kwarg which is cleaned up afterwards"""

    @wraps(func)
    def new_func(*args, **kwargs):
        with mgg.workbench_manager.create() as workbench:
            return func(*args, workbench=workbench, **kwargs)

    return new_func


def allow_registration(controller):
    """ Decorator for if registration is enabled"""
    @wraps(controller)
    def wrapper(request, *args, **kwargs):
        if not mgg.app_config["allow_registration"]:
            messages.add_message(
                request,
                messages.WARNING,
                _('Sorry, registration is disabled on this instance.'))
            return redirect(request, "index")

        return controller(request, *args, **kwargs)

    return wrapper

def allow_reporting(controller):
    """ Decorator for if reporting is enabled"""
    @wraps(controller)
    def wrapper(request, *args, **kwargs):
        if not mgg.app_config["allow_reporting"]:
            messages.add_message(
                request,
                messages.WARNING,
                _('Sorry, reporting is disabled on this instance.'))
            return redirect(request, 'index')

        return controller(request, *args, **kwargs)

    return wrapper

def get_optional_media_comment_by_id(controller):
    """
    Pass in a MediaComment based off of a url component. Because of this decor-
    -ator's use in filing Media or Comment Reports, it has two valid outcomes.

    :returns        The view function being wrapped with kwarg `comment` set to
                        the MediaComment who's id is in the URL. If there is a
                        comment id in the URL and if it is valid.
    :returns        The view function being wrapped with kwarg `comment` set to
                        None. If there is no comment id in the URL.
    :returns        A 404 Error page, if there is a comment if in the URL and it
                        is invalid.
    """
    @wraps(controller)
    def wrapper(request, *args, **kwargs):
        if 'comment' in request.matchdict:
            comment = MediaComment.query.filter_by(
                    id=request.matchdict['comment']).first()

            if comment is None:
                return render_404(request)

            return controller(request, comment=comment, *args, **kwargs)
        else:
            return controller(request, comment=None, *args, **kwargs)
    return wrapper


def auth_enabled(controller):
    """Decorator for if an auth plugin is enabled"""
    @wraps(controller)
    def wrapper(request, *args, **kwargs):
        if not mgg.app.auth:
            messages.add_message(
                request,
                messages.WARNING,
                _('Sorry, authentication is disabled on this instance.'))
            return redirect(request, 'index')

        return controller(request, *args, **kwargs)

    return wrapper

def require_admin_or_moderator_login(controller):
    """
    Require a login from an administrator or a moderator.
    """
    @wraps(controller)
    def new_controller_func(request, *args, **kwargs):
        if request.user and \
            not (request.user.has_privilege(u'admin')
                or request.user.has_privilege(u'moderator')):

            raise Forbidden()
        elif not request.user:
            next_url = urljoin(
                    request.urlgen('mediagoblin.auth.login',
                        qualified=True),
                    request.url)

            return redirect(request, 'mediagoblin.auth.login',
                            next=next_url)

        return controller(request, *args, **kwargs)

    return new_controller_func



def oauth_required(controller):
    """ Used to wrap API endpoints where oauth is required """
    @wraps(controller)
    def wrapper(request, *args, **kwargs):
        data = request.headers
        authorization = decode_authorization_header(data)

        if authorization == dict():
            error = "Missing required parameter."
            return json_response({"error": error}, status=400)


        request_validator = GMGRequestValidator()
        resource_endpoint = ResourceEndpoint(request_validator)
        valid, r = resource_endpoint.validate_protected_resource_request(
                uri=request.base_url,
                http_method=request.method,
                body=request.data,
                headers=dict(request.headers),
                )

        if not valid:
            error = "Invalid oauth prarameter."
            return json_response({"error": error}, status=400)

        # Fill user if not already
        token = authorization[u"oauth_token"]
        request.access_token = AccessToken.query.filter_by(token=token).first()
        if request.access_token is not None and request.user is None:
            user_id = request.access_token.user
            request.user = User.query.filter_by(id=user_id).first()

        return controller(request, *args, **kwargs)

    return wrapper
