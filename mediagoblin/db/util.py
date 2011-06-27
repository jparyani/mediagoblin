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
Utilities for database operations.

Some note on migration and indexing tools:

We store information about what the state of the database is in the
'mediagoblin' document of the 'app_metadata' collection.  Keys in that
document relevant to here:

 - 'migration_number': The integer representing the current state of
   the migrations
"""

import copy

# Imports that other modules might use
from pymongo import DESCENDING
from pymongo.errors import InvalidId
from mongokit import ObjectId

from mediagoblin.db.indexes import ACTIVE_INDEXES, DEPRECATED_INDEXES


def add_new_indexes(database, active_indexes=ACTIVE_INDEXES):
    """
    Add any new indexes to the database.

    Returns:
      A list of indexes added in form ('collection', 'index_name')
    """
    indexes_added = []

    for collection_name, indexes in active_indexes.iteritems():
        collection = database[collection_name]
        collection_indexes = collection.index_information().keys()

        for index_name, index_data in indexes.iteritems():
            if not index_name in collection_indexes:
                # Get a copy actually so we don't modify the actual
                # structure
                index_data = copy.copy(index_data)
                index = index_data.pop('index')
                collection.create_index(
                    index, name=index_name, **index_data)

                indexes_added.append((collection_name, index_name))

    return indexes_added


def remove_deprecated_indexes(database, deprecated_indexes=DEPRECATED_INDEXES):
    """
    Remove any deprecated indexes from the database.

    Returns:
      A list of indexes removed in form ('collection', 'index_name')
    """
    indexes_removed = []

    for collection_name, indexes in deprecated_indexes.iteritems():
        collection = database[collection_name]
        collection_indexes = collection.index_information().keys()

        for index_name, index_data in indexes.iteritems():
            if index_name in collection_indexes:
                collection.drop_index(index_name)

                indexes_removed.append((collection_name, index_name))

    return indexes_removed
