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

from email.MIMEText import MIMEText
import smtplib
import sys

import jinja2
import mongokit


TESTS_ENABLED = False
def _activate_testing():
    """
    Call this to activate testing in util.py
    """
    global TESTS_ENABLED
    TESTS_ENABLED = True


def get_jinja_env(user_template_path=None):
    """
    Set up the Jinja environment, possibly allowing for user
    overridden templates.

    (In the future we may have another system for providing theming;
    for now this is good enough.)
    """
    if user_template_path:
        loader = jinja2.ChoiceLoader(
            [jinja2.FileSystemLoader(user_template_path),
             jinja2.PackageLoader('mediagoblin', 'templates')])
    else:
        loader = jinja2.PackageLoader('mediagoblin', 'templates')

    return jinja2.Environment(loader=loader, autoescape=True)


def setup_user_in_request(request):
    """
    Examine a request and tack on a request.user parameter if that's
    appropriate.
    """
    if not request.session.has_key('user_id'):
        request.user = None
        return

    user = None
    user = request.app.db.User.one(
        {'_id': mongokit.ObjectId(request.session['user_id'])})

    if not user:
        # Something's wrong... this user doesn't exist?  Invalidate
        # this session.
        request.session.invalidate()

    request.user = user


def import_component(import_string):
    """
    Import a module component defined by STRING.  Probably a method,
    class, or global variable.

    Args:
     - import_string: a string that defines what to import.  Written
       in the format of "module1.module2:component"
    """
    module_name, func_name = import_string.split(':', 1)
    __import__(module_name)
    module = sys.modules[module_name]
    func = getattr(module, func_name)
    return func


### ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
### Special email test stuff begins HERE
### ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# We have two "test inboxes" here:
# 
# EMAIL_TEST_INBOX:
# ----------------
#   If you're writing test views, you'll probably want to check this.
#   It contains a list of MIMEText messages.
#
# EMAIL_TEST_MBOX_INBOX:
# ----------------------
#   This collects the messages from the FakeMhost inbox.  It's reslly
#   just here for testing the send_email method itself.
#
#   Anyway this contains:
#    - from
#    - to: a list of email recipient addresses
#    - message: not just the body, but the whole message, including
#      headers, etc.
#
# ***IMPORTANT!***
# ----------------
# Before running tests that call functions which send email, you should
# always call _clear_test_inboxes() to "wipe" the inboxes clean. 

EMAIL_TEST_INBOX = []
EMAIL_TEST_MBOX_INBOX = []


class FakeMhost(object):
    """
    Just a fake mail host so we can capture and test messages
    from send_email
    """
    def connect(self):
        pass

    def sendmail(self, from_addr, to_addrs, message):
        EMAIL_TEST_MBOX_INBOX.append(
            {'from': from_addr,
             'to': to_addrs,
             'message': message})

def _clear_test_inboxes():
    global EMAIL_TEST_INBOX
    global EMAIL_TEST_MBOX_INBOX
    EMAIL_TEST_INBOX = []
    EMAIL_TEST_MBOX_INBOX = []

### ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
### </Special email test stuff>
### ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def send_email(from_addr, to_addrs, subject, message_body):
    """
    Simple email sending wrapper, use this so we can capture messages
    for unit testing purposes.

    Args:
     - from_addr: address you're sending the email from
     - to_addrs: list of recipient email addresses
     - subject: subject of the email
     - message_body: email body text
    """
    # TODO: make a mock mhost if testing is enabled
    if TESTS_ENABLED:
        mhost = FakeMhost()
    else:
        mhost = smtplib.SMTP()

    mhost.connect()

    message = MIMEText(message_body.encode('utf-8'), 'plain', 'utf-8')
    message['Subject'] = subject
    message['From'] = from_addr
    # The shorthand condition takes height for the possibility that the to_addrs argument can be either list() or string()
    message['To'] = ', '.join(to_addrs) if type( to_addrs ) == list else to_addrs

    if TESTS_ENABLED:
        EMAIL_TEST_INBOX.append(message)

    return mhost.sendmail(from_addr, to_addrs, message.as_string())
