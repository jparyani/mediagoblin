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
from mediagoblin import mg_globals
from mediagoblin.db import migrations
from mediagoblin.db.util import ASCENDING, DESCENDING, ObjectId
from mediagoblin.util import Pagination

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
        'url' : unicode,
        'bio' : unicode
        }

    required_fields = ['username', 'created', 'pw_hash', 'email']

    default_values = {
        'created': datetime.datetime.utcnow,
        'email_verified': False,
        'status': u'needs_email_verification',
        'verification_key': lambda: unicode(uuid.uuid4()),
        'is_admin': False}
        
    migration_handler = migrations.UserMigration

    def check_login(self, password):
        """
        See if a user can login with this password
        """
        return auth_lib.bcrypt_check_password(
            password, self['pw_hash'])


class MediaEntry(Document):
    __collection__ = 'media_entries'

    structure = {
        'uploader': ObjectId,
        'title': unicode,
        'slug': unicode,
        'created': datetime.datetime,
        'description': unicode, # May contain markdown/up
        'description_html': unicode, # May contain plaintext, or HTML
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

    def main_mediafile(self):
        pass
    
    def get_comments(self, page):
        cursor = self.db.MediaComment.find({
                'media_entry': self['_id']}).sort('created', DESCENDING)
        
        pagination = Pagination(page, cursor)
        comments = pagination()
        
        data = list()
        for comment in comments:
            comment['author'] = self.db.User.find_one({
                    '_id': comment['author']})
            data.append(comment)
            
        return (data, pagination)
        
    def generate_slug(self):
        self['slug'] = util.slugify(self['title'])

        duplicate = mg_globals.database.media_entries.find_one(
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
            
    def url_to_prev(self, urlgen):
        """
        Provide a url to the previous entry from this user, if there is one
        """
        cursor = self.db.MediaEntry.find({'_id' : {"$lt": self['_id']}, 
                                          'uploader': self['uploader']}).sort(
                                                    '_id', DESCENDING).limit(1)
                                                    
        if cursor.count():
            return urlgen('mediagoblin.user_pages.media_home',
                          user=self.uploader()['username'],
                          media=unicode(cursor[0]['_id']))
        
    def url_to_next(self, urlgen):
        """
        Provide a url to the next entry from this user, if there is one
        """
        cursor = self.db.MediaEntry.find({'_id' : {"$gt": self['_id']}, 
                                          'uploader': self['uploader']}).sort(
                                                    '_id', ASCENDING).limit(1)

        if cursor.count():
            return urlgen('mediagoblin.user_pages.media_home',
                          user=self.uploader()['username'],
                          media=unicode(cursor[0]['_id']))

    def uploader(self):
        return self.db.User.find_one({'_id': self['uploader']})

class MediaComment(Document):
    __collection__ = 'media_comments'

    structure = {
        'media_entry': ObjectId,
        'author': ObjectId,
        'created': datetime.datetime,
        'content': unicode,
        'content_html': unicode}

    required_fields = [
        'media_entry', 'author', 'created', 'content']

    default_values = {
        'created': datetime.datetime.utcnow}

    def media_entry(self):
        return self.db.MediaEntry.find_one({'_id': self['media_entry']})

    def author(self):
        return self.db.User.find_one({'_id': self['author']})

REGISTER_MODELS = [
    MediaEntry,
    User,
    MediaComment]


def register_models(connection):
    """
    Register all models in REGISTER_MODELS with this connection.
    """
    connection.register(REGISTER_MODELS)

