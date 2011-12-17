from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mediagoblin.init import setup_global_and_app_config, setup_database
from mediagoblin.db.util import ObjectId

from mediagoblin.db.sql.models import (Base, User, MediaEntry, MediaComment,
    Tag, MediaTag)

Session = sessionmaker()


obj_id_table = dict()

def add_obj_ids(entry, new_entry):
    global obj_id_table
    print "%r -> %r" % (entry._id, new_entry.id)
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

    for entry in mk_db.User.find():
        print entry.username

        new_entry = User()
        copy_attrs(entry, new_entry,
            ('username', 'email', 'created', 'pw_hash', 'email_verified',
             'status', 'verification_key', 'is_admin', 'url',
             'bio', 'bio_html',
             'fp_verification_key', 'fp_token_expire',))
        # new_entry.fp_verification_expire = entry.fp_token_expire

        session.add(new_entry)
        session.flush()
        add_obj_ids(entry, new_entry)

    session.commit()
    session.close()


def convert_media_entries(mk_db):
    session = Session()

    for entry in mk_db.MediaEntry.find():
        print repr(entry.title)

        new_entry = MediaEntry()
        copy_attrs(entry, new_entry,
            ('title', 'slug', 'created',
             'description', 'description_html',
             'media_type',
             'fail_error',
             'queued_task_id',))
        copy_reference_attr(entry, new_entry, "uploader")

        session.add(new_entry)
        session.flush()
        add_obj_ids(entry, new_entry)

    session.commit()
    session.close()


def convert_media_tags(mk_db):
    session = Session()
    session.autoflush = False

    for media in mk_db.MediaEntry.find():
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

    for entry in mk_db.MediaComment.find():
        print repr(entry.content)

        new_entry = MediaComment()
        copy_attrs(entry, new_entry,
            ('created',
             'content', 'content_html',))
        copy_reference_attr(entry, new_entry, "media_entry")
        copy_reference_attr(entry, new_entry, "author")

        session.add(new_entry)
        session.flush()
        add_obj_ids(entry, new_entry)

    session.commit()
    session.close()


def main():
    engine = create_engine('sqlite:///mediagoblin.db', echo=True)
    Session.configure(bind=engine)

    setup_global_and_app_config("mediagoblin.ini")

    mk_conn, mk_db = setup_database()

    Base.metadata.create_all(engine)

    convert_users(mk_db)
    convert_media_entries(mk_db)
    convert_media_tags(mk_db)
    convert_media_comments(mk_db)


if __name__ == '__main__':
    main()
