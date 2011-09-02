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
In some places, we need to access the database, public_store, queue_store
"""

import gettext
import pkg_resources


#############################
# General mediagoblin globals
#############################

# mongokit.Connection
db_connection = None

# mongokit.Connection
database = None

# should be the same as the 
public_store = None
queue_store = None

# A WorkBenchManager
workbench_manager = None

# gettext
translations = gettext.find(
    'mediagoblin',
    pkg_resources.resource_filename(
    'mediagoblin', 'translations'), ['en'])

# app and global config objects
app_config = None
global_config = None

# The actual app object
app = None


def setup_globals(**kwargs):
    """
    Sets up a bunch of globals in this module.

    Takes the globals to setup as keyword arguments.  If globals are
    specified that aren't set as variables above, then throw an error.
    """
    from mediagoblin import mg_globals

    for key, value in kwargs.iteritems():
        if not hasattr(mg_globals, key):
            raise AssertionError("Global %s not known" % key)
        setattr(mg_globals, key, value)
