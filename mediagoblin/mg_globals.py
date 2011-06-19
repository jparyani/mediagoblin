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

# Dump mail to stdout instead of sending it:
email_debug_mode = False

# Address for sending out mails
email_sender_address = None

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
    from mediagoblin import mg_globals

    for key, value in kwargs.iteritems():
        if not hasattr(mg_globals, key):
            raise AssertionError("Global %s not known" % key)
        setattr(mg_globals, key, value)
