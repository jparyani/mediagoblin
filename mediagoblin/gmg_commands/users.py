import os

from mediagoblin.gmg_commands import util as commands_util
from mediagoblin.db.open import setup_connection_and_db_from_config
from mediagoblin.auth import lib as auth_lib
from mediagoblin import mg_globals

def adduser_usage():
    print '\nUsage: adduser -u username -p password -m email'


def adduser_parser_setup(subparser):
    subparser.add_argument(
        '-u', '--username',
        help="Username used to login")
    subparser.add_argument(
        '-p', '--password',
        help="Your supersecret word to login")
    subparser.add_argument(
        '-m', '--email',
        help="Email to recieve notifications")
    subparser.add_argument(
        '-cf', '--conf_file', default='mediagoblin.ini',
        help="Config file used to set up environment")


def adduser(args):
    #TODO: Lets trust admins this do not validate Emails :)
    if args.username == None :
        print 'You must provide an username'
        adduser_usage()
    elif args.password == None:
        print 'You must provide a password'
        adduser_usage()
    elif args.email == None:
        print 'You must provide an email'
        adduser_usage()
    else:
        mgoblin_app = commands_util.setup_app(args)

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
            entry['email_verified'] = True
            entry.save(validate=True)

            print "User Created: Already Verified :)"


def makeadmin_usage():
    print '\nUsage: makeadmin -u username'


def makeadmin_parser_setup(subparser):
    subparser.add_argument(
        '-u', '--username',
        help="Username to give admin level")
    subparser.add_argument(
        '-cf', '--conf_file', default='mediagoblin.ini',
        help="Config file used to set up environment")


def makeadmin(args):
    if args.username == None:
        print 'You must provide an username'
        makeadmin_usage()
    else:
        mgoblin_app = commands_util.setup_app(args)

        db = mg_globals.database

        user = db.User.one({'username':unicode(args.username.lower())})
        if user:
            user['is_admin'] = True
            user.save()
            print 'The user is now Admin'
        else:
            print 'The user doesn\'t exist'


def changepw_usage():
    print '\nUsage: changepw -u username -p new_password'


def changepw_parser_setup(subparser):
    subparser.add_argument(
        '-u', '--username',
        help="Username used to login")
    subparser.add_argument(
        '-p', '--password',
        help="Your NEW supersecret word to login")
    subparser.add_argument(
        '-cf', '--conf_file', default='mediagoblin.ini',
        help="Config file used to set up environment")


def changepw(args):
    if args.username == None:
        print 'You must provide an username'
        adduser_usage()
    elif args.password == None:
        print 'You must provide a password'
        adduser_usage()
    else:
        mgoblin_app = commands_util.setup_app(args)

        db = mg_globals.database

        user = db.User.one({'username':unicode(args.username.lower())})
        if user:
            user['pw_hash'] = auth_lib.bcrypt_gen_password_hash(args.password)
            user.save()
            print 'Password successfully changed'
        else:
            print 'The user doesn\'t exist'

