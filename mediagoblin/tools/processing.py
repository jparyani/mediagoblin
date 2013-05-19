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

import logging
import json
import traceback

from urllib2 import urlopen, Request, HTTPError
from urllib import urlencode

_log = logging.getLogger(__name__)

TESTS_CALLBACKS = {}


def create_post_request(url, data, **kw):
    '''
    Issue a HTTP POST request.

    Args:
        url: The URL to which the POST request should be issued
        data: The data to be send in the body of the request
        **kw:
        data_parser: The parser function that is used to parse the `data`
            argument
    '''
    data_parser = kw.get('data_parser', urlencode)
    headers = kw.get('headers', {})

    return Request(url, data_parser(data), headers=headers)


def json_processing_callback(entry):
    '''
    Send an HTTP post to the registered callback url, if any.
    '''
    if not entry.processing_metadata:
        _log.debug('No processing callback for {0}'.format(entry))
        return

    url = entry.processing_metadata[0].callback_url

    _log.debug('Sending processing callback for {0} ({1})'.format(
        entry,
        url))

    headers = {
            'Content-Type': 'application/json'}

    data = {
            'id': entry.id,
            'state': entry.state}

    # Trigger testing mode, no callback will be sent
    if url.endswith('secrettestmediagoblinparam'):
        TESTS_CALLBACKS.update({url: data})
        return True

    request = create_post_request(
            url,
            data,
            headers=headers,
            data_parser=json.dumps)

    try:
        urlopen(request)
        _log.debug('Processing callback for {0} sent'.format(entry))

        return True
    except HTTPError:
        _log.error('Failed to send callback: {0}'.format(
            traceback.format_exc()))

        return False
