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

from mediagoblin.tools import common

DEBUG = 'debug'
INFO = 'info'
SUCCESS = 'success'
WARNING = 'warning'
ERROR = 'error'

ADD_MESSAGE_TEST = []


def add_message(request, level, text):
    messages = request.session.setdefault('messages', [])
    messages.append({'level': level, 'text': text})

    if common.TESTS_ENABLED:
        ADD_MESSAGE_TEST.append(messages)

    request.session.save()


def fetch_messages(request, clear_from_session=True):
    messages = request.session.get('messages')
    if messages and clear_from_session:
        # Save that we removed the messages from the session
        request.session['messages'] = []
        request.session.save()

    return messages


def clear_add_message():
    global ADD_MESSAGE_TEST
    ADD_MESSAGE_TEST = []
