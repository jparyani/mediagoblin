#!./bin/python

import pymongo
import sys, os

print "*** WARNING! ***"
print "  Running this will destroy your mediagoblin database,"
print "  remove all your media files in user_dev/, etc."

drop_it = raw_input(
    'Are you SURE you want to destroy your environment? (if so, type "yes")> ')

if not drop_it == 'yes':
    sys.exit(1)

conn = pymongo.Connection()
conn.drop_database('mediagoblin')

os.popen('rm -rf user_dev/media')
os.popen('rm -rf user_dev/beaker')

print "removed all your stuff!  okay, now re-run ./bin/buildout"
