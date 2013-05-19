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
from __future__ import unicode_literals
import logging
import re

from mediagoblin import meddleware

_log = logging.getLogger(__name__)

class TrimWhiteSpaceMeddleware(meddleware.BaseMeddleware):
    _setup_plugin_called = 0
    RE_MULTI_WHITESPACE = re.compile(b'(\s)\s+', re.M)

    def process_response(self, request, response):
        """Perform very naive html tidying by removing multiple whitespaces"""
        # werkzeug.BaseResponse has no content_type attr, this comes via
        # werkzeug.wrappers.CommonRequestDescriptorsMixin (part of
        # wrappers.Response)
        if getattr(response ,'content_type', None) != 'text/html':
            return

        # This is a tad more complex than needed to be able to handle
        # response.data and response.body, depending on whether we have
        # a werkzeug Resonse or a webob one. Let's kill webob soon!
        if hasattr(response, 'body') and not hasattr(response, 'data'):
            # Old-style webob Response object.
            # TODO: Remove this once we transition away from webob
            resp_attr = 'body'
        else:
            resp_attr = 'data'
            # Don't flatten iterator to list when we fudge the response body
            # (see werkzeug.Response documentation)
            response.implicit_sequence_conversion = False

        # Set the tidied text. Very naive tidying for now, just strip all
        # subsequent whitespaces (this preserves most newlines)
        setattr(response, resp_attr, re.sub(
                TrimWhiteSpaceMeddleware.RE_MULTI_WHITESPACE, br'\1',
                getattr(response, resp_attr)))

    @classmethod
    def setup_plugin(cls):
        """Set up this meddleware as a plugin during 'setup' hook"""
        global _log
        if cls._setup_plugin_called:
            _log.info('Trim whitespace plugin was already set up.')
            return

        _log.debug('Trim whitespace plugin set up.')
        cls._setup_plugin_called += 1

        # Append ourselves to the list of enabled Meddlewares
        meddleware.ENABLED_MEDDLEWARE.append(
            '{0}:{1}'.format(cls.__module__, cls.__name__))


hooks = {
    'setup': TrimWhiteSpaceMeddleware.setup_plugin
    }
