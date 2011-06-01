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

import datetime, uuid

from mongokit import Document, Set

from mediagoblin import util
from mediagoblin.auth import lib as auth_lib
from mediagoblin import globals as mediagoblin_globals
from mediagoblin.db import migrations
from mediagoblin.db.util import ObjectId

###################
# Custom validators
###################

########
# Models
########


class User(Document):
    __collection__ = 'users'

    structure = {
        'username': unicode,
        'email': unicode,
        'created': datetime.datetime,
        'plugin_data': dict, # plugins can dump stuff here.
        'pw_hash': unicode,
        'email_verified': bool,
        'status': unicode,
        'verification_key': unicode,
        'is_admin': bool,
        }

    required_fields = ['username', 'created', 'pw_hash', 'email']

    default_values = {
        'created': datetime.datetime.utcnow,
        'email_verified': False,
        'status': u'needs_email_verification',
        'verification_key': lambda: unicode(uuid.uuid4()),
        'is_admin': False}

    def check_login(self, password):
        """
        See if a user can login with this password
        """
        return auth_lib.bcrypt_check_password(
            password, self['pw_hash'])

    def generate_new_verification_key(self):
        """
        Create a new verification key, overwriting the old one.
        """

        self['verification_key'] = unicode(uuid.uuid4())
        self.save(validate=False)


class MediaEntry(Document):
    __collection__ = 'media_entries'

    structure = {
        'uploader': ObjectId,
        'title': unicode,
        'slug': unicode,
        'created': datetime.datetime,
        'description': unicode,
        'media_type': unicode,
        'media_data': dict, # extra data relevant to this media_type
        'plugin_data': dict, # plugins can dump stuff here.
        'tags': [unicode],
        'state': unicode,

        # For now let's assume there can only be one main file queued
        # at a time
        'queued_media_file': [unicode],

        # A dictionary of logical names to filepaths
        'media_files': dict,

        # The following should be lists of lists, in appropriate file
        # record form
        'attachment_files': list,

        # This one should just be a single file record
        'thumbnail_file': [unicode]}

    required_fields = [
        'uploader', 'created', 'media_type', 'slug']

    default_values = {
        'created': datetime.datetime.utcnow,
        'state': u'unprocessed'}

    migration_handler = migrations.MediaEntryMigration

    indexes = [
        # Referene uniqueness of slugs by uploader
        {'fields': ['uploader', 'slug'],
         'unique': True}]

    def main_mediafile(self):
        pass

    def generate_slug(self):
        self['slug'] = util.slugify(self['title'])

        duplicate = mediagoblin_globals.database.media_entries.find_one(
            {'slug': self['slug']})
        
        if duplicate:
            self['slug'] = "%s-%s" % (self['_id'], self['slug'])

    def url_for_self(self, urlgen):
        """
        Generate an appropriate url for ourselves

        Use a slug if we have one, else use our '_id'.
        """
        uploader = self.uploader()

        if self.get('slug'):
            return urlgen(
                'mediagoblin.user_pages.media_home',
                user=uploader['username'],
                media=self['slug'])
        else:
            return urlgen(
                'mediagoblin.user_pages.media_home',
                user=uploader['username'],
                media=unicode(self['_id']))

    def uploader(self):
        return self.db.User.find_one({'_id': self['uploader']})


REGISTER_MODELS = [MediaEntry, User]


def register_models(connection):
    """
    Register all models in REGISTER_MODELS with this connection.
    """
    connection.register(REGISTER_MODELS)

