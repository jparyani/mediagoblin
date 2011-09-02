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

from mediagoblin.gmg_commands import util as commands_util
from mediagoblin.auth import lib as auth_lib
from mediagoblin import mg_globals


def adduser_parser_setup(subparser):
    subparser.add_argument(
        'username',
        help="Username used to login")
    subparser.add_argument(
        'password',
        help="Your supersecret word to login")
    subparser.add_argument(
        'email',
        help="Email to recieve notifications")
    subparser.add_argument(
        '-cf', '--conf_file', default='mediagoblin.ini',
        help="Config file used to set up environment")


def adduser(args):
    #TODO: Lets trust admins this do not validate Emails :)
    commands_util.setup_app(args)

    db = mg_globals.database
    users_with_username = \
        db.User.find({
            'username': args.username.lower()
        }).count()

    if users_with_username:
        print u'Sorry, a user with that name already exists.'

    else:
        # Create the user
        entry = db.User()
        entry['username'] = unicode(args.username.lower())
        entry['email'] = unicode(args.email)
        entry['pw_hash'] = auth_lib.bcrypt_gen_password_hash(args.password)
        entry['status'] = u'active'
        entry['email_verified'] = True
        entry.save(validate=True)

        print "User created (and email marked as verified)"


def makeadmin_parser_setup(subparser):
    subparser.add_argument(
        'username',
        help="Username to give admin level")
    subparser.add_argument(
        '-cf', '--conf_file', default='mediagoblin.ini',
        help="Config file used to set up environment")


def makeadmin(args):
    commands_util.setup_app(args)

    db = mg_globals.database

    user = db.User.one({'username':unicode(args.username.lower())})
    if user:
        user['is_admin'] = True
        user.save()
        print 'The user is now Admin'
    else:
        print 'The user doesn\'t exist'


def changepw_parser_setup(subparser):
    subparser.add_argument(
        'username',
        help="Username used to login")
    subparser.add_argument(
        'password',
        help="Your NEW supersecret word to login")
    subparser.add_argument(
        '-cf', '--conf_file', default='mediagoblin.ini',
        help="Config file used to set up environment")


def changepw(args):
    commands_util.setup_app(args)

    db = mg_globals.database

    user = db.User.one({'username':unicode(args.username.lower())})
    if user:
        user['pw_hash'] = auth_lib.bcrypt_gen_password_hash(args.password)
        user.save()
        print 'Password successfully changed'
    else:
        print 'The user doesn\'t exist'

