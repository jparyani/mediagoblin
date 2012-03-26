# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
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

import sys
import pymongo
import sys
import os
import shutil

from mediagoblin.init import setup_global_and_app_config


def wipe_parser_setup(subparser):
    pass


def wipe(args):
    global_config, app_config = setup_global_and_app_config(args.conf_file)

    print "*** WARNING! ***"
    print ""
    print "Running this will destroy your mediagoblin database,"
    print "remove all your media files in user_dev/, etc."
    print ""
    print "ALSO: This command is currently a hack and will only remove"
    print "  things properly on the default setup!  If you've customized"
    print "  your mediagoblin configs, it won't work (for now)."

    drop_it = raw_input(
        'Are you **SURE** you want to destroy your environment?  '
        '(if so, type "yes")> ')

    if drop_it != 'yes':
        return

    print "nixing data in mongodb...."
    conn = pymongo.Connection()
    conn.drop_database(app_config["db_name"])

    for directory in [os.path.join(os.getcwd(), "user_dev", "media"),
                      os.path.join(os.getcwd(), "user_dev", "beaker")]:
        if os.path.exists(directory):
            print "nixing %s...." % directory
            shutil.rmtree(directory)

    print "removed all your stuff!"
