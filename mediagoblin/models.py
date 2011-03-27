# GNU Mediagoblin -- federated, autonomous media hosting
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

from mongokit import Document, Set

import datetime


class MediaEntry(Document):
    __collection__ = 'media_entries'

    structure = {
        'title': unicode,
        'created': datetime.datetime,
        'description': unicode,
        'media_type': unicode,
        'media_data': dict, # extra data relevant to this media_type
        'plugin_data': dict, # plugins can dump stuff here.
        'file_store': unicode,
        'attachments': [dict],
        'tags': [unicode]}

    required_fields = [
        'title', 'created',
        'media_type', 'file_store']

    default_values = {
        'created': datetime.datetime.utcnow}

    def main_mediafile(self):
        pass

class User(Document):
    structure = {
        'username': unicode,
        'created': datetime.datetime,
        'plugin_data': dict, # plugins can dump stuff here.
        'pw_hash': unicode,
        }

    required_fields = ['username', 'created', 'pw_hash']

    default_values = {
        'created': datetime.datetime.utcnow}


REGISTER_MODELS = [MediaEntry, User]


def register_models(connection):
    """
    Register all models in REGISTER_MODELS with this connection.
    """
    connection.register(REGISTER_MODELS)

