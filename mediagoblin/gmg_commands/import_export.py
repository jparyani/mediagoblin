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

from mediagoblin import mg_globals
from mediagoblin.db.open import setup_connection_and_db_from_config
from mediagoblin.gmg_commands import util as commands_util
from mediagoblin.storage.filestorage import BasicFileStorage
from mediagoblin.init import setup_storage, setup_global_and_app_config

import shutil
import tarfile
import tempfile
import subprocess
import os.path
import os
import sys
import logging
from contextlib import closing

_log = logging.getLogger('gmg.import_export')
logging.basicConfig()
_log.setLevel(logging.INFO)


def import_export_parse_setup(subparser):
    # TODO: Add default
    subparser.add_argument(
        'tar_file')
    subparser.add_argument(
        '--mongodump_path', default='mongodump',
        help='mongodump binary')
    subparser.add_argument(
        '--mongorestore_path', default='mongorestore',
        help='mongorestore binary')
    subparser.add_argument(
        '--cache_path',
        help='Temporary directory where files will be temporarily dumped')


def _import_media(db, args):
    '''
    Import media files

    Must be called after _import_database()
    '''
    _log.info('-> Importing media...')

    media_cache = BasicFileStorage(
        args._cache_path['media'])

    # TODO: Add import of queue files
    queue_cache = BasicFileStorage(args._cache_path['queue'])

    for entry in db.MediaEntry.query.filter_by():
        for name, path in entry.media_files.items():
            _log.info('Importing: {0} - {1}'.format(
                    entry.title.encode('ascii', 'replace'),
                    name))

            media_file = mg_globals.public_store.get_file(path, mode='wb')
            media_file.write(
                media_cache.get_file(path, mode='rb').read())

    _log.info('...Media imported')


def _import_database(db, args):
    '''
    Restore mongo database from ___.bson files
    '''
    _log.info('-> Importing database...')

    p = subprocess.Popen([
            args.mongorestore_path,
            '-d', db.name,
            os.path.join(args._cache_path['database'], db.name)])

    p.wait()

    _log.info('...Database imported')


def env_import(args):
    '''
    Restore mongo database and media files from a tar archive
    '''
    if not args.cache_path:
        args.cache_path = tempfile.mkdtemp()

    setup_global_and_app_config(args.conf_file)

    # Creates mg_globals.public_store and mg_globals.queue_store
    setup_storage()

    global_config, app_config = setup_global_and_app_config(args.conf_file)
    db = setup_connection_and_db_from_config(
        app_config)

    tf = tarfile.open(
        args.tar_file,
        mode='r|gz')

    tf.extractall(args.cache_path)

    args.cache_path = os.path.join(
        args.cache_path, 'mediagoblin-data')
    args = _setup_paths(args)

    # Import database from extracted data
    _import_database(db, args)

    _import_media(db, args)

    _clean(args)


def _setup_paths(args):
    '''
    Populate ``args`` variable with cache subpaths
    '''
    args._cache_path = dict()
    PATH_MAP = {
        'media': 'media',
        'queue': 'queue',
        'database': 'database'}

    for key, val in PATH_MAP.items():
        args._cache_path[key] = os.path.join(args.cache_path, val)

    return args


def _create_archive(args):
    '''
    Create the tar archive
    '''
    _log.info('-> Compressing to archive')

    tf = tarfile.open(
        args.tar_file,
        mode='w|gz')

    with closing(tf):
        tf.add(args.cache_path, 'mediagoblin-data/')

    _log.info('...Archiving done')


def _clean(args):
    '''
    Remove cache directory
    '''
    shutil.rmtree(args.cache_path)


def _export_check(args):
    '''
    Run security checks for export command
    '''
    if os.path.exists(args.tar_file):
        overwrite = raw_input(
            'The output file already exists. '
            'Are you **SURE** you want to overwrite it? '
            '(yes/no)> ')
        if not overwrite == 'yes':
            print 'Aborting.'

            return False

    return True


def _export_database(db, args):
    _log.info('-> Exporting database...')

    p = subprocess.Popen([
            args.mongodump_path,
            '-d', db.name,
            '-o', args._cache_path['database']])

    p.wait()

    _log.info('...Database exported')


def _export_media(db, args):
    _log.info('-> Exporting media...')

    media_cache = BasicFileStorage(
        args._cache_path['media'])

    # TODO: Add export of queue files
    queue_cache = BasicFileStorage(args._cache_path['queue'])

    for entry in db.MediaEntry.query.filter_by():
        for name, path in entry.media_files.items():
            _log.info(u'Exporting {0} - {1}'.format(
                    entry.title,
                    name))
            try:
                mc_file = media_cache.get_file(path, mode='wb')
                mc_file.write(
                    mg_globals.public_store.get_file(path, mode='rb').read())
            except Exception as e:
                _log.error('Failed: {0}'.format(e))

    _log.info('...Media exported')


def env_export(args):
    '''
    Export database and media files to a tar archive
    '''
    commands_util.check_unrecognized_args(args)
    if args.cache_path:
        if os.path.exists(args.cache_path):
            _log.error('The cache directory must not exist '
                       'before you run this script')
            _log.error('Cache directory: {0}'.format(args.cache_path))

            return False
    else:
        args.cache_path = tempfile.mkdtemp()

    args = _setup_paths(args)

    if not _export_check(args):
        _log.error('Checks did not pass, exiting')
        sys.exit(0)

    globa_config, app_config = setup_global_and_app_config(args.conf_file)

    setup_storage()

    db = setup_connection_and_db_from_config(app_config)

    _export_database(db, args)

    _export_media(db, args)

    _create_archive(args)

    _clean(args)
