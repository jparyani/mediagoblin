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

from mediagoblin.util import cleaned_markdown_conversion

from mongokit import DocumentMigration


class MediaEntryMigration(DocumentMigration):
    def allmigration01_uploader_to_reference(self):
        """
        Old MediaEntry['uploader'] accidentally embedded the User instead
        of referencing it.  Fix that!
        """
        # uploader is an associative array
        self.target = {'uploader': {'$type': 3}}
        if not self.status:
            for doc in self.collection.find(self.target):
                self.update = {
                    '$set': {
                        'uploader': doc['uploader']['_id']}}
                self.collection.update(
                    self.target, self.update, multi=True, safe=True)

    def allmigration02_add_description_html(self):
        """
        Now that we can have rich descriptions via Markdown, we should
        update all existing entries to record the rich description versions.
        """
        self.target = {'description_html': {'$exists': False}}

        if not self.status:
            for doc in self.collection.find(self.target):
                self.update = {
                    '$set': {
                        'description_html': cleaned_markdown_conversion(
                            doc['description'])}}
        
class UserMigration(DocumentMigration):
    def allmigration01_add_bio_and_url_profile(self):
        """
        User can elaborate profile with home page and biography
        """
        self.target = {'url': {'$exists': False},
                       'bio': {'$exists': False}}
        if not self.status:
            for doc in self.collection.find(self.target):
                self.update = {
                    '$set': {'url': '', 
                             'bio': ''}}
                self.collection.update(
                    self.target, self.update, multi=True, safe=True)
                        
                        
MIGRATE_CLASSES = ['MediaEntry', 'User']
