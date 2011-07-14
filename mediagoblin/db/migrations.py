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

from mediagoblin.db.util import RegisterMigration
from mediagoblin.util import cleaned_markdown_conversion


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
