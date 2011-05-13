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

# gettext
translations = gettext.find(
    'mediagoblin',
    pkg_resources.resource_filename(
    'mediagoblin', 'translations'), ['en'])


def setup_globals(**kwargs):
    from mediagoblin import globals as mg_globals

    for key, value in kwargs.iteritems():
        setattr(mg_globals, key, value)
