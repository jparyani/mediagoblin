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

from __future__ import print_function, unicode_literals

import six
import smtplib
import sys
from mediagoblin import mg_globals, messages
from mediagoblin._compat import MIMEText
from mediagoblin.tools import common

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
    def login(self, *args, **kwargs):
        pass

    def sendmail(self, from_addr, to_addrs, message):
        EMAIL_TEST_MBOX_INBOX.append(
            {'from': from_addr,
             'to': to_addrs,
             'message': message})

    def starttls(self):
        raise smtplib.SMTPException("No STARTTLS here")

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
    if common.TESTS_ENABLED or mg_globals.app_config['email_debug_mode']:
        mhost = FakeMhost()
    elif not mg_globals.app_config['email_debug_mode']:
        if mg_globals.app_config['email_smtp_use_ssl']:
            smtp_init = smtplib.SMTP_SSL
        else:
            smtp_init = smtplib.SMTP

        mhost = smtp_init(
            mg_globals.app_config['email_smtp_host'],
            mg_globals.app_config['email_smtp_port'])

        # SMTP.__init__ Issues SMTP.connect implicitly if host
        if not mg_globals.app_config['email_smtp_host']:  # e.g. host = ''
            mhost.connect()  # We SMTP.connect explicitly

        try:
            mhost.starttls()
        except smtplib.SMTPException:
            # Only raise an exception if we're forced to
            if mg_globals.app_config['email_smtp_force_starttls']:
                six.reraise(*sys.exc_info())

    if ((not common.TESTS_ENABLED)
        and (mg_globals.app_config['email_smtp_user']
             or mg_globals.app_config['email_smtp_pass'])):
        mhost.login(
            mg_globals.app_config['email_smtp_user'],
            mg_globals.app_config['email_smtp_pass'])

    message = MIMEText(message_body.encode('utf-8'), 'plain', 'utf-8')
    message['Subject'] = subject
    message['From'] = from_addr
    message['To'] = ', '.join(to_addrs)

    if common.TESTS_ENABLED:
        EMAIL_TEST_INBOX.append(message)

    elif mg_globals.app_config['email_debug_mode']:
        print("===== Email =====")
        print("From address: %s" % message['From'])
        print("To addresses: %s" % message['To'])
        print("Subject: %s" % message['Subject'])
        print("-- Body: --")
        print(message.get_payload(decode=True))

    return mhost.sendmail(from_addr, to_addrs, message.as_string())


def normalize_email(email):
    """return case sensitive part, lower case domain name

    :returns: None in case of broken email addresses"""
    try:
        em_user, em_dom = email.split('@', 1)
    except ValueError:
        # email contained no '@'
        return None
    email = "@".join((em_user, em_dom.lower()))
    return email


def email_debug_message(request):
    """
    If the server is running in email debug mode (which is
    the current default), give a debug message to the user
    so that they have an idea where to find their email.
    """
    if mg_globals.app_config['email_debug_mode']:
        # DEBUG message, no need to translate
        messages.add_message(request, messages.DEBUG,
            "This instance is running in email debug mode. "
            "The email will be on the console of the server process.")
