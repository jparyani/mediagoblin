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

from copy import copy
from itertools import chain, imap

from mediagoblin.init import setup_global_and_app_config

from mediagoblin.db.sql.base import Session
from mediagoblin.db.sql.models_v0 import Base_v0
from mediagoblin.db.sql.models_v0 import (User, MediaEntry, MediaComment,
    Tag, MediaTag, MediaFile, MediaAttachmentFile, MigrationData,
    ImageData, VideoData, AsciiData, AudioData)
from mediagoblin.db.sql.open import setup_connection_and_db_from_config as \
    sql_connect
from mediagoblin.db.mongo.open import setup_connection_and_db_from_config as \
    mongo_connect


obj_id_table = dict()


def add_obj_ids(entry, new_entry):
    global obj_id_table
    print "\t%r -> SQL id %r" % (entry._id, new_entry.id)
    obj_id_table[entry._id] = new_entry.id


def copy_attrs(entry, new_entry, attr_list):
    for a in attr_list:
        val = entry[a]
        setattr(new_entry, a, val)


def copy_reference_attr(entry, new_entry, ref_attr):
    val = entry[ref_attr]
    val = obj_id_table[val]
    setattr(new_entry, ref_attr, val)


def convert_users(mk_db):
    session = Session()

    for entry in mk_db.User.find().sort('created'):
        print entry.username

        new_entry = User()
        copy_attrs(entry, new_entry,
            ('username', 'email', 'created', 'pw_hash', 'email_verified',
             'status', 'verification_key', 'is_admin', 'url',
             'bio',
             'fp_verification_key', 'fp_token_expire',))
        # new_entry.fp_verification_expire = entry.fp_token_expire

        session.add(new_entry)
        session.flush()
        add_obj_ids(entry, new_entry)

    session.commit()
    session.close()


def convert_media_entries(mk_db):
    session = Session()

    for entry in mk_db.MediaEntry.find().sort('created'):
        print repr(entry.title)

        new_entry = MediaEntry()
        copy_attrs(entry, new_entry,
            ('title', 'slug', 'created',
             'description',
             'media_type', 'state', 'license',
             'fail_error', 'fail_metadata',
             'queued_task_id',))
        copy_reference_attr(entry, new_entry, "uploader")

        session.add(new_entry)
        session.flush()
        add_obj_ids(entry, new_entry)

        for key, value in entry.media_files.iteritems():
            new_file = MediaFile(name=key, file_path=value)
            new_file.media_entry = new_entry.id
            Session.add(new_file)

        for attachment in entry.attachment_files:
            new_attach = MediaAttachmentFile(
                name=attachment["name"],
                filepath=attachment["filepath"],
                created=attachment["created"]
                )
            new_attach.media_entry = new_entry.id
            Session.add(new_attach)

    session.commit()
    session.close()


def convert_image(mk_db):
    session = Session()

    for media in mk_db.MediaEntry.find(
            {'media_type': 'mediagoblin.media_types.image'}).sort('created'):
        media_data = copy(media.media_data)

        if len(media_data):
            media_data_row = ImageData(**media_data)
            media_data_row.media_entry = obj_id_table[media['_id']]
            session.add(media_data_row)

    session.commit()
    session.close()


def convert_video(mk_db):
    session = Session()

    for media in mk_db.MediaEntry.find(
            {'media_type': 'mediagoblin.media_types.video'}).sort('created'):
        media_data_row = VideoData(**media.media_data)
        media_data_row.media_entry = obj_id_table[media['_id']]
        session.add(media_data_row)

    session.commit()
    session.close()


def convert_media_tags(mk_db):
    session = Session()
    session.autoflush = False

    for media in mk_db.MediaEntry.find().sort('created'):
        print repr(media.title)

        for otag in media.tags:
            print "  ", repr((otag["slug"], otag["name"]))

            nslug = session.query(Tag).filter_by(slug=otag["slug"]).first()
            print "     ", repr(nslug)
            if nslug is None:
                nslug = Tag(slug=otag["slug"])
                session.add(nslug)
                session.flush()
            print "     ", repr(nslug), nslug.id

            ntag = MediaTag()
            ntag.tag = nslug.id
            ntag.name = otag["name"]
            ntag.media_entry = obj_id_table[media._id]
            session.add(ntag)

    session.commit()
    session.close()


def convert_media_comments(mk_db):
    session = Session()

    for entry in mk_db.MediaComment.find().sort('created'):
        print repr(entry.content)

        new_entry = MediaComment()
        copy_attrs(entry, new_entry,
            ('created',
             'content',))

        try:
            copy_reference_attr(entry, new_entry, "media_entry")
            copy_reference_attr(entry, new_entry, "author")
        except KeyError as e:
            print('KeyError in convert_media_comments(): {0}'.format(e))
        else:
            session.add(new_entry)
            session.flush()
            add_obj_ids(entry, new_entry)

    session.commit()
    session.close()


media_types_tables = (
    ("mediagoblin.media_types.image", (ImageData,)),
    ("mediagoblin.media_types.video", (VideoData,)),
    ("mediagoblin.media_types.ascii", (AsciiData,)),
    ("mediagoblin.media_types.audio", (AudioData,)),
    )


def convert_add_migration_versions(dummy_sql_db):
    session = Session()

    for name in chain(("__main__",),
                      imap(lambda e: e[0], media_types_tables)):
        print "\tAdding %s" % (name,)
        m = MigrationData(name=unicode(name), version=0)
        session.add(m)

    session.commit()
    session.close()


def cleanup_sql_tables(sql_db):
    for mt, table_list in media_types_tables:
        session = Session()

        count = session.query(MediaEntry.media_type). \
            filter_by(media_type=unicode(mt)).count()
        print "  %s: %d entries" % (mt, count)

        if count == 0:
            print "\tAnalyzing tables"
            for tab in table_list:
                cnt2 = session.query(tab).count()
                print "\t  %s: %d entries" % (tab.__tablename__, cnt2)
                assert cnt2 == 0

            print "\tRemoving migration info"
            mi = session.query(MigrationData).filter_by(name=unicode(mt)).one()
            session.delete(mi)
            session.commit()
            session.close()

            print "\tDropping tables"
            tables = [model.__table__ for model in table_list]
            Base_v0.metadata.drop_all(sql_db.engine, tables=tables)

        session.close()


def print_header(title):
    print "\n=== %s ===" % (title,)


convert_call_list = (
    ("Converting Users", convert_users),
    ("Converting Media Entries", convert_media_entries),
    ("Converting Media Data for Images", convert_image),
    ("Cnnverting Media Data for Videos", convert_video),
    ("Converting Tags for Media", convert_media_tags),
    ("Converting Media Comments", convert_media_comments),
    )

sql_call_list = (
    ("Filling Migration Tables", convert_add_migration_versions),
    ("Analyzing/Cleaning SQL Data", cleanup_sql_tables),
    )

def run_conversion(config_name):
    global_config, app_config = setup_global_and_app_config(config_name)

    sql_conn, sql_db = sql_connect(app_config)
    mk_conn, mk_db = mongo_connect(app_config)

    Base_v0.metadata.create_all(sql_db.engine)

    for title, func in convert_call_list:
        print_header(title)
        func(mk_db)
        Session.remove()
    
    for title, func in sql_call_list:
        print_header(title)
        func(sql_db)
        Session.remove()


if __name__ == '__main__':
    run_conversion("mediagoblin.ini")
