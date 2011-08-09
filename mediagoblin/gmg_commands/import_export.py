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

from mediagoblin.gmg_commands import util as commands_util
from mediagoblin import mg_globals
from mediagoblin.db import util as db_util
from mediagoblin.db.open import setup_connection_and_db_from_config
from mediagoblin.init.config import read_mediagoblin_config
from mediagoblin import util as mg_util
from mediagoblin.storage import BasicFileStorage
from mediagoblin.init import setup_storage, setup_global_and_app_config

import shlex
import tarfile
import subprocess
import os.path
import os
import re

def import_export_parse_setup(subparser):
    # TODO: Add default
    subparser.add_argument(
        'tar_file')
    subparser.add_argument(
        '-cf', '--conf_file', default='mediagoblin.ini',
        help='Config file used to set up environment')
    subparser.add_argument(
        '--mongodump_path', default='mongodump',
        help='mongodump binary')
    subparser.add_argument(
        '--mongorestore_path', default='mongorestore',
        help='mongorestore binary')
    subparser.add_argument(
        '--cache_path', default='/tmp/mediagoblin/',
        help='')

def _export_database(db, args):
    print "\n== Exporting database ==\n"
    
    command = '{mongodump_path} -d {database} -o {mongodump_cache}'.format(
        mongodump_path=args.mongodump_path,
        database=db.name,
        mongodump_cache=args._cache_path['database'])
    
    p = subprocess.Popen(
        shlex.split(command))
    
    p.wait()

    print "\n== Database exported ==\n"

def _export_media(db, args):
    
    print "\n== Exporting media ==\n"
    
    media_cache = BasicFileStorage(
        args._cache_path['media'])

    for entry in db.media_entries.find():
        for name, path in entry['media_files'].items():
            mc_file = media_cache.get_file(path, mode='wb')
            mc_file.write(
                mg_globals.public_store.get_file(path, mode='rb').read())

            print(mc_file)
        print(entry)

    queue_cache = BasicFileStorage(
        args._cache_path['queue'])

    qc_file = queue_cache.get_file(entry['queued_media_file'], mode='wb')
    qc_file.write(
        mg_globals.queue_store.get_file(entry['queued_media_file'], mode='rb').read())
    print(qc_file)

    print "\n== Media exported ==\n"

def _import_database(db, args):
    command = '{mongorestore_path} -d {database} -o {mongodump_cache}'.format(
        mongorestore_path=args.mongorestore_path,
        database=db.name,
        mongodump_cache=args.mongodump_cache)

def env_import(args):
    config, validation_result = read_mediagoblin_config(args.conf_file)
    connection, db = setup_connection_and_db_from_config(
        config['mediagoblin'], use_pymongo=True)

    tf = tarfile.open(
        args.tar_file,
        mode='r|gz')

    tf.extractall(args.extract_path)

def _setup_paths(args):
    args._cache_path = dict()
    PATH_MAP = {
        'media': 'media',
        'queue': 'queue', 
        'database': 'database'}
    
    for key, val in PATH_MAP.items():
        args._cache_path[key] = os.path.join(args.cache_path, val)

    return args

def _create_archive(args):
    print "\n== Compressing to archive ==\n"
    tf = tarfile.open(
        args.tar_file,
        mode='w|gz')
    with tf: 
        for root, dirs, files in os.walk(args.cache_path):
            print root, dirs, files

            everything = []
            everything.extend(dirs)
            everything.extend(files)

            print everything

            for d in everything:
                directory_path = os.path.join(root, d)
                virtual_path = os.path.join(
                    root.replace(args.cache_path, 'mediagoblin-data/'), d)

                # print 'dir', directory_path, '\n', 'vir', virtual_path

                tarinfo = tf.gettarinfo(
                    directory_path,
                    arcname=virtual_path)

                tf.addfile(tarinfo)

                print 'added ', d

    '''
    mg_data = tf.gettarinfo(
        args.cache_path, 
        arcname='mediagoblin-data')
    
    tf.addfile(mg_data)
    '''
    print "\n== Archiving done ==\n"

def env_export(args):
    args = _setup_paths(args)

    setup_global_and_app_config(args.conf_file)
    setup_storage()

    config, validation_result = read_mediagoblin_config(args.conf_file)
    connection, db = setup_connection_and_db_from_config(
        config['mediagoblin'], use_pymongo=True)

    if os.path.exists(args.tar_file):
        overwrite = raw_input(
            'The output file already exists. '
            'Are you **SURE** you want to overwrite it? '
            '(yes/no)> ')
        if not overwrite == 'yes':
            print "Aborting."
            return

    _export_database(db, args)

    _export_media(db, args)

    _create_archive(args)
