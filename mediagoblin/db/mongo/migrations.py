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

from mediagoblin.db.mongo.util import RegisterMigration
from mediagoblin.tools.text import cleaned_markdown_conversion


def add_table_field(db, table_name, field_name, default_value):
    """
    Add a new field to the table/collection named table_name.
    The field will have the name field_name and the value default_value
    """
    db[table_name].update(
        {field_name: {'$exists': False}},
        {'$set': {field_name: default_value}},
        multi=True)


def drop_table_field(db, table_name, field_name):
    """
    Drop an old field from a table/collection
    """
    db[table_name].update(
        {field_name: {'$exists': True}},
        {'$unset': {field_name: 1}},
        multi=True)


# Please see mediagoblin/tests/test_migrations.py for some examples of
# basic migrations.


@RegisterMigration(1)
def user_add_bio_html(database):
    """
    Users now have richtext bios via Markdown, reflect appropriately.
    """
    collection = database['users']

    target = collection.find(
        {'bio_html': {'$exists': False}})

    for document in target:
        document['bio_html'] = cleaned_markdown_conversion(
            document['bio'])
        collection.save(document)


@RegisterMigration(2)
def mediaentry_mediafiles_main_to_original(database):
    """
    Rename "main" media file to "original".
    """
    collection = database['media_entries']
    target = collection.find(
        {'media_files.main': {'$exists': True}})

    for document in target:
        original = document['media_files'].pop('main')
        document['media_files']['original'] = original

        collection.save(document)


@RegisterMigration(3)
def mediaentry_remove_thumbnail_file(database):
    """
    Use media_files['thumb'] instead of media_entries['thumbnail_file']
    """
    database['media_entries'].update(
        {'thumbnail_file': {'$exists': True}},
        {'$unset': {'thumbnail_file': 1}},
        multi=True)


@RegisterMigration(4)
def mediaentry_add_queued_task_id(database):
    """
    Add the 'queued_task_id' field for entries that don't have it.
    """
    add_table_field(database, 'media_entries', 'queued_task_id', None)


@RegisterMigration(5)
def mediaentry_add_fail_error_and_metadata(database):
    """
    Add 'fail_error' and 'fail_metadata' fields to media entries
    """
    add_table_field(database, 'media_entries', 'fail_error', None)
    add_table_field(database, 'media_entries', 'fail_metadata', {})


@RegisterMigration(6)
def user_add_forgot_password_token_and_expires(database):
    """
    Add token and expiration fields to help recover forgotten passwords
    """
    add_table_field(database, 'users', 'fp_verification_key', None)
    add_table_field(database, 'users', 'fp_token_expire', None)


@RegisterMigration(7)
def media_type_image_to_multimedia_type_image(database):
    database['media_entries'].update(
        {'media_type': 'image'},
        {'$set': {'media_type': 'mediagoblin.media_types.image'}},
        multi=True)


@RegisterMigration(8)
def mediaentry_add_license(database):
    """
    Add the 'license' field for entries that don't have it.
    """
    add_table_field(database, 'media_entries', 'license', None)


@RegisterMigration(9)
def remove_calculated_html(database):
    """
    Drop pre-rendered html again and calculate things
    on the fly (and cache):
    - User.bio_html
    - MediaEntry.description_html
    - MediaComment.content_html
    """
    drop_table_field(database, 'users', 'bio_html')
    drop_table_field(database, 'media_entries', 'description_html')
    drop_table_field(database, 'media_comments', 'content_html')


@RegisterMigration(10)
def convert_video_media_data(database):
    """
    Move media_data["video"] directly into media_data
    """
    collection = database['media_entries']
    target = collection.find(
        {'media_data.video': {'$exists': True}})

    for document in target:
        assert len(document['media_data']) == 1
        document['media_data'] = document['media_data']['video']
        collection.save(document)


@RegisterMigration(11)
def convert_gps_media_data(database):
    """
    Move media_data["gps"]["*"] to media_data["gps_*"].
    In preparation for media_data.gps_*
    """
    collection = database['media_entries']
    target = collection.find(
        {'media_data.gps': {'$exists': True}})

    for document in target:
        for key, value in document['media_data']['gps'].iteritems():
            document['media_data']['gps_' + key] = value
        del document['media_data']['gps']
        collection.save(document)


@RegisterMigration(12)
def convert_exif_media_data(database):
    """
    Move media_data["exif"]["clean"] to media_data["exif_all"].
    Drop media_data["exif"]["useful"]
    In preparation for media_data.exif_all
    """
    collection = database['media_entries']
    target = collection.find(
        {'media_data.exif.clean': {'$exists': True}})

    for document in target:
        media_data = document['media_data']

        exif_all = media_data['exif'].pop('clean')
        if len(exif_all):
            media_data['exif_all'] = exif_all

        del media_data['exif']['useful']

        assert len(media_data['exif']) == 0
        del media_data['exif']

        collection.save(document)


@RegisterMigration(13)
def user_add_wants_comment_notification(database):
    """
    Add wants_comment_notification to user model
    """
    add_table_field(database, 'users', 'wants_comment_notification', True)
