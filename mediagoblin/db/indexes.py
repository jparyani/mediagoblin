# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 MediaGoblin contributors.  See AUTHORS.
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

"""
Indexes for the local database.

To add new indexes
------------------

Indexes are recorded in the following format:

ACTIVE_INDEXES = {
    'collection_name': {
        'identifier': {  # key identifier used for possibly deprecating later
            'index': [index_foo_goes_here]}}

... and anything else being parameters to the create_index function
(including unique=True, etc)

Current indexes must be registered in ACTIVE_INDEXES... deprecated
indexes should be marked in DEPRECATED_INDEXES.

Remember, ordering of compound indexes MATTERS.  Read below for more.

REQUIRED READING:
 - http://kylebanker.com/blog/2010/09/21/the-joy-of-mongodb-indexes/

 - http://www.mongodb.org/display/DOCS/Indexes
 - http://www.mongodb.org/display/DOCS/Indexing+Advice+and+FAQ


To remove deprecated indexes
----------------------------

Removing deprecated indexes is the same, just move the index into the
deprecated indexes mapping.

DEPRECATED_INDEXES = {
    'collection_name': {
        'deprecated_index_identifier1': {
            'index': [index_foo_goes_here]}}
        
... etc.

If an index has been deprecated that identifier should NEVER BE USED
AGAIN.  Eg, if you previously had 'awesomepants_unique', you shouldn't
use 'awesomepants_unique' again, you should create a totally new name
or at worst use 'awesomepants_unique2'.
"""

from pymongo import ASCENDING, DESCENDING


################
# Active indexes
################
ACTIVE_INDEXES = {}

# MediaEntry indexes
# ------------------

MEDIAENTRY_INDEXES = {
    'uploader_slug_unique': {
        # Matching an object to an uploader + slug.
        # MediaEntries are unique on these two combined, eg:
        #   /u/${myuser}/m/${myslugname}/
        'index': [('uploader', ASCENDING),
                  ('slug', ASCENDING)],
        'unique': True},

    'created': {
        # A global index for all media entries created, in descending
        # order.  This is used for the site's frontpage.
        'index': [('created', DESCENDING)]},

    'uploader_created': {
        # Indexing on uploaders and when media entries are created.
        # Used for showing a user gallery, etc.
        'index': [('uploader', ASCENDING),
                  ('created', DESCENDING)]},

    'state_uploader_tags_created': {
        # Indexing on processed?, media uploader, associated tags, and timestamp
        # Used for showing media items matching a tag search, most recent first.
        'index': [('state', ASCENDING),
                  ('uploader', ASCENDING),
                  ('tags.slug', DESCENDING),
                  ('created', DESCENDING)]},

    'state_tags_created': {
        # Indexing on processed?, media tags, and timestamp (across all users)
        # This is used for a front page tag search.
        'index': [('state', ASCENDING),
                  ('tags.slug', DESCENDING),
                  ('created', DESCENDING)]}}


ACTIVE_INDEXES['media_entries'] = MEDIAENTRY_INDEXES


# User indexes
# ------------

USER_INDEXES = {
    'username_unique': {
        # Index usernames, and make sure they're unique.
        # ... I guess we might need to adjust this once we're federated :)
        'index': 'username',
        'unique': True},
    'created': {
        # All most recently created users
        'index': 'created'}}


ACTIVE_INDEXES['users'] = USER_INDEXES


# MediaComment indexes

MEDIA_COMMENT_INDEXES = {
   'mediaentry_created': {
        'index': [('media_entry', ASCENDING),
                  ('created', DESCENDING)]}}

ACTIVE_INDEXES['media_comments'] = MEDIA_COMMENT_INDEXES


####################
# Deprecated indexes
####################

DEPRECATED_INDEXES = {}
