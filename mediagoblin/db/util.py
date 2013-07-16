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

from mediagoblin.db.base import Session
from mediagoblin.db.models import MediaEntry, Tag, MediaTag, Collection


##########################
# Random utility functions
##########################


def atomic_update(table, query_dict, update_values):
    table.query.filter_by(**query_dict).update(update_values,
    	synchronize_session=False)
    Session.commit()


def check_media_slug_used(uploader_id, slug, ignore_m_id):
    query = MediaEntry.query.filter_by(uploader=uploader_id, slug=slug)
    if ignore_m_id is not None:
        query = query.filter(MediaEntry.id != ignore_m_id)
    does_exist = query.first() is not None
    return does_exist


def media_entries_for_tag_slug(dummy_db, tag_slug):
    return MediaEntry.query \
        .join(MediaEntry.tags_helper) \
        .join(MediaTag.tag_helper) \
        .filter(
            (MediaEntry.state == u'processed')
            & (Tag.slug == tag_slug))


def clean_orphan_tags(commit=True):
    """Search for unused MediaTags and delete them"""
    q1 = Session.query(Tag).outerjoin(MediaTag).filter(MediaTag.id==None)
    for t in q1:
        Session.delete(t)
    # The "let the db do all the work" version:
    # q1 = Session.query(Tag.id).outerjoin(MediaTag).filter(MediaTag.id==None)
    # q2 = Session.query(Tag).filter(Tag.id.in_(q1))
    # q2.delete(synchronize_session = False)
    if commit:
        Session.commit()


def check_collection_slug_used(creator_id, slug, ignore_c_id):
    filt = (Collection.creator == creator_id) \
        & (Collection.slug == slug)
    if ignore_c_id is not None:
        filt = filt & (Collection.id != ignore_c_id)
    does_exist = Session.query(Collection.id).filter(filt).first() is not None
    return does_exist


if __name__ == '__main__':
    from mediagoblin.db.open import setup_connection_and_db_from_config

    db = setup_connection_and_db_from_config({'sql_engine':'sqlite:///mediagoblin.db'})

    clean_orphan_tags()
