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

# Maybe not every model needs a test, but some models have special
# methods, and so it makes sense to test them here.

from mediagoblin.db.base import Session
from mediagoblin.db.models import MediaEntry, User, Privilege

from mediagoblin.tests.tools import fixture_add_user

import mock


class FakeUUID(object):
    hex = 'testtest-test-test-test-testtesttest'

UUID_MOCK = mock.Mock(return_value=FakeUUID())


class TestMediaEntrySlugs(object):
    def _setup(self):
        self.chris_user = fixture_add_user(u'chris')
        self.emily_user = fixture_add_user(u'emily')
        self.existing_entry = self._insert_media_entry_fixture(
            title=u"Beware, I exist!",
            slug=u"beware-i-exist")

    def _insert_media_entry_fixture(self, title=None, slug=None, this_id=None,
                                    uploader=None, save=True):
        entry = MediaEntry()
        entry.title = title or u"Some title"
        entry.slug = slug
        entry.id = this_id
        entry.uploader = uploader or self.chris_user.id
        entry.media_type = u'image'

        if save:
            entry.save()

        return entry

    def test_unique_slug_from_title(self, test_app):
        self._setup()

        entry = self._insert_media_entry_fixture(u"Totally unique slug!", save=False)
        entry.generate_slug()
        assert entry.slug == u'totally-unique-slug'

    def test_old_good_unique_slug(self, test_app):
        self._setup()

        entry = self._insert_media_entry_fixture(
            u"A title here", u"a-different-slug-there", save=False)
        entry.generate_slug()
        assert entry.slug == u"a-different-slug-there"

    def test_old_weird_slug(self, test_app):
        self._setup()

        entry = self._insert_media_entry_fixture(
            slug=u"wowee!!!!!", save=False)
        entry.generate_slug()
        assert entry.slug == u"wowee"

    def test_existing_slug_use_id(self, test_app):
        self._setup()

        entry = self._insert_media_entry_fixture(
            u"Beware, I exist!!", this_id=9000, save=False)
        entry.generate_slug()
        assert entry.slug == u"beware-i-exist-9000"

    def test_existing_slug_cant_use_id(self, test_app):
        self._setup()

        # Getting tired of dealing with test_app and this mock.patch
        # thing conflicting, getting lazy.
        @mock.patch('uuid.uuid4', UUID_MOCK)
        def _real_test():
            # This one grabs the nine thousand slug
            self._insert_media_entry_fixture(
                slug=u"beware-i-exist-9000")

            entry = self._insert_media_entry_fixture(
                u"Beware, I exist!!", this_id=9000, save=False)
            entry.generate_slug()
            assert entry.slug == u"beware-i-exist-test"

        _real_test()

    def test_existing_slug_cant_use_id_extra_junk(self, test_app):
        self._setup()

        # Getting tired of dealing with test_app and this mock.patch
        # thing conflicting, getting lazy.
        @mock.patch('uuid.uuid4', UUID_MOCK)
        def _real_test():
            # This one grabs the nine thousand slug
            self._insert_media_entry_fixture(
                slug=u"beware-i-exist-9000")

            # This one grabs makes sure the annoyance doesn't stop
            self._insert_media_entry_fixture(
                slug=u"beware-i-exist-test")

            entry = self._insert_media_entry_fixture(
                 u"Beware, I exist!!", this_id=9000, save=False)
            entry.generate_slug()
            assert entry.slug == u"beware-i-exist-testtest"

        _real_test()

    def test_garbage_slug(self, test_app):
        """
        Titles that sound totally like Q*Bert shouldn't have slugs at
        all.  We'll just reference them by id.

                  ,
                 / \      (@!#?@!)
                |\,/|   ,-,  /
                | |#|  ( ")~
               / \|/ \  L L
              |\,/|\,/|
              | |#, |#|
             / \|/ \|/ \
            |\,/|\,/|\,/|
            | |#| |#| |#|
           / \|/ \|/ \|/ \
          |\,/|\,/|\,/|\,/|
          | |#| |#| |#| |#|
           \|/ \|/ \|/ \|/
        """
        self._setup()

        qbert_entry = self._insert_media_entry_fixture(
            u"@!#?@!", save=False)
        qbert_entry.generate_slug()
        assert qbert_entry.slug is None

class TestUserHasPrivilege:
    def _setup(self):
        fixture_add_user(u'natalie',
            privileges=[u'admin',u'moderator',u'active'])
        fixture_add_user(u'aeva',
            privileges=[u'moderator',u'active'])
        self.natalie_user = User.query.filter(
            User.username==u'natalie').first()
        self.aeva_user = User.query.filter(
            User.username==u'aeva').first()

    def test_privilege_added_correctly(self, test_app):
        self._setup()
        admin = Privilege.query.filter(
            Privilege.privilege_name == u'admin').one()
        # first make sure the privileges were added successfully

        assert admin in self.natalie_user.all_privileges
        assert admin not in self.aeva_user.all_privileges

    def test_user_has_privilege_one(self, test_app):
        self._setup()

        # then test out the user.has_privilege method for one privilege
        assert not self.natalie_user.has_privilege(u'commenter')
        assert self.aeva_user.has_privilege(u'active')


    def test_user_has_privileges_multiple(self, test_app):
        self._setup()

        # when multiple args are passed to has_privilege,  the method returns
        # True if the user has ANY of the privileges
        assert self.natalie_user.has_privilege(u'admin',u'commenter')
        assert self.aeva_user.has_privilege(u'moderator',u'active')
        assert not self.natalie_user.has_privilege(u'commenter',u'uploader')



def test_media_data_init(test_app):
    Session.rollback()
    Session.remove()
    media = MediaEntry()
    media.media_type = u"mediagoblin.media_types.image"
    assert media.media_data is None
    media.media_data_init()
    assert media.media_data is not None
    obj_in_session = 0
    for obj in Session():
        obj_in_session += 1
        print repr(obj)
    assert obj_in_session == 0

