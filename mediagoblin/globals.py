"""
In some places, we need to access the database, public_store, queue_store
"""

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


def setup_globals(**kwargs):
    from mediagoblin import globals as mg_globals

    for key, value in kwargs.iteritems():
        setattr(mg_globals, key, value)
