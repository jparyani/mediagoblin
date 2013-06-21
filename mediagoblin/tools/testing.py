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

from mediagoblin.tools import common
from mediagoblin.tools.template import clear_test_template_context
from mediagoblin.tools.mail import EMAIL_TEST_INBOX, EMAIL_TEST_MBOX_INBOX

def _activate_testing():
    """
    Call this to activate testing in util.py
    """

    common.TESTS_ENABLED = True

def clear_test_buckets():
    """
    We store some things for testing purposes that should be cleared
    when we want a "clean slate" of information for our next round of
    tests.  Call this function to wipe all that stuff clean.

    Also wipes out some other things we might redefine during testing,
    like the jinja envs.
    """
    global SETUP_JINJA_ENVS
    SETUP_JINJA_ENVS = {}

    global EMAIL_TEST_INBOX
    global EMAIL_TEST_MBOX_INBOX
    EMAIL_TEST_INBOX = []
    EMAIL_TEST_MBOX_INBOX = []

    clear_test_template_context()
