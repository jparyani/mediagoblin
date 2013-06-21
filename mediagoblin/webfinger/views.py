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
'''
For references, see docstring in mediagoblin/webfinger/__init__.py
'''

import re

from urlparse import urlparse

from mediagoblin.tools.response import render_to_response, render_404

def host_meta(request):
    '''
    Webfinger host-meta
    '''

    placeholder = 'MG_LRDD_PLACEHOLDER'

    lrdd_title = 'GNU MediaGoblin - User lookup'

    lrdd_template = request.urlgen(
        'mediagoblin.webfinger.xrd',
        uri=placeholder,
        qualified=True)

    return render_to_response(
        request,
        'mediagoblin/webfinger/host-meta.xml',
        {'request': request,
         'lrdd_template': lrdd_template,
         'lrdd_title': lrdd_title,
         'placeholder': placeholder})

MATCH_SCHEME_PATTERN = re.compile(r'^acct:')

def xrd(request):
    ''' 
    Find user data based on a webfinger URI
    '''
    param_uri = request.GET.get('uri')

    if not param_uri:
        return render_404(request)

    '''
    :py:module:`urlparse` does not recognize usernames in URIs of the
    form ``acct:user@example.org`` or ``user@example.org``.
    '''
    if not MATCH_SCHEME_PATTERN.search(param_uri):
        # Assume the URI is in the form ``user@example.org``
        uri = 'acct://' + param_uri
    else:
        # Assumes the URI looks like ``acct:user@example.org
        uri = MATCH_SCHEME_PATTERN.sub(
            'acct://', param_uri)

    parsed = urlparse(uri)

    xrd_subject = param_uri

    # TODO: Verify that the user exists
    # Q: Does webfinger support error handling in this case?
    #    Returning 404 seems intuitive, need to check.
    if parsed.username:
        # The user object
        # TODO: Fetch from database instead of using the MockUser
        user = MockUser()
        user.username = parsed.username

        xrd_links = [
            {'attrs': {
                    'rel': 'http://microformats.org/profile/hcard',
                    'href': request.urlgen(
                        'mediagoblin.user_pages.user_home',
                        user=user.username,
                        qualified=True)}},
            {'attrs': {
                    'rel': 'http://schemas.google.com/g/2010#updates-from',
                    'href': request.urlgen(
                        'mediagoblin.user_pages.atom_feed',
                        user=user.username,
                        qualified=True)}}]

        xrd_alias = request.urlgen(
            'mediagoblin.user_pages.user_home',
            user=user.username,
            qualified=True)

        return render_to_response(
            request,
            'mediagoblin/webfinger/xrd.xml',
            {'request': request,
             'subject': xrd_subject,
             'alias': xrd_alias,
             'links': xrd_links })
    else:
        return render_404(request)

class MockUser(object):
    '''
    TEMPORARY user object
    '''
    username = None
