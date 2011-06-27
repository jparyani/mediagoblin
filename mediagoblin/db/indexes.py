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

"""
Indexes for the local database.

Indexes are recorded in the following format:

INDEXES = {
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


####################
# Deprecated indexes
####################

# @@: Do we really need to keep the index form if we're removing by
# key name? I guess it's helpful to keep the record...


DEPRECATED_INDEXES = {}
