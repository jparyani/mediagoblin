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
import gettext
import pkg_resources
import smtplib
import sys

import jinja2
import mongokit

from mediagoblin import globals as mgoblin_globals


TESTS_ENABLED = False
def _activate_testing():
    """
    Call this to activate testing in util.py
    """
    global TESTS_ENABLED
    TESTS_ENABLED = True


def get_jinja_loader(user_template_path=None):
    """
    Set up the Jinja template loaders, possibly allowing for user
    overridden templates.

    (In the future we may have another system for providing theming;
    for now this is good enough.)
    """
    if user_template_path:
        return jinja2.ChoiceLoader(
            [jinja2.FileSystemLoader(user_template_path),
             jinja2.PackageLoader('mediagoblin', 'templates')])
    else:
        return jinja2.PackageLoader('mediagoblin', 'templates')


def get_jinja_env(template_loader, locale):
    """
    Set up the Jinja environment, 

    (In the future we may have another system for providing theming;
    for now this is good enough.)
    """
    setup_gettext(locale)

    template_env = jinja2.Environment(
        loader=template_loader, autoescape=True,
        extensions=['jinja2.ext.i18n'])

    template_env.install_gettext_callables(
        mgoblin_globals.translations.gettext,
        mgoblin_globals.translations.ngettext)

    return template_env


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
    if TESTS_ENABLED or mgoblin_globals.email_debug_mode:
        mhost = FakeMhost()
    elif not mgoblin_globals.email_debug_mode:
        mhost = smtplib.SMTP()

    mhost.connect()

    message = MIMEText(message_body.encode('utf-8'), 'plain', 'utf-8')
    message['Subject'] = subject
    message['From'] = from_addr
    message['To'] = ', '.join(to_addrs)

    if TESTS_ENABLED:
        EMAIL_TEST_INBOX.append(message)

    if getattr(mgoblin_globals, 'email_debug_mode', False):
        print u"===== Email ====="
        print u"From address: %s" % message['From']
        print u"To addresses: %s" % message['To']
        print u"Subject: %s" % message['Subject']
        print u"-- Body: --"
        print message.get_payload(decode=True)

    return mhost.sendmail(from_addr, to_addrs, message.as_string())


###################
# Translation tools
###################


TRANSLATIONS_PATH = pkg_resources.resource_filename(
    'mediagoblin', 'translations')


def locale_to_lower_upper(locale):
    """
    Take a locale, regardless of style, and format it like "en-us"
    """
    if '-' in locale:
        lang, country = locale.split('-', 1)
        return '%s_%s' % (lang.lower(), country.upper())
    elif '_' in locale:
        lang, country = locale.split('_', 1)
        return '%s_%s' % (lang.lower(), country.upper())
    else:
        return locale.lower()


def locale_to_lower_lower(locale):
    """
    Take a locale, regardless of style, and format it like "en_US"
    """
    if '_' in locale:
        lang, country = locale.split('_', 1)
        return '%s-%s' % (lang.lower(), country.lower())
    else:
        return locale.lower()


def get_locale_from_request(request):
    """
    Figure out what target language is most appropriate based on the
    request
    """
    request_form = request.GET or request.POST

    if request_form.has_key('lang'):
        return locale_to_lower_upper(request_form['lang'])

    accept_lang_matches = request.accept_language.best_matches()

    # Your routing can explicitly specify a target language
    if request.matchdict.has_key('locale'):
        target_lang = request.matchdict['locale']
    elif request.session.has_key('target_lang'):
        target_lang = request.session['target_lang']
    # Pull the first acceptable language
    elif accept_lang_matches:
        target_lang = accept_lang_matches[0]
    # Fall back to English
    else:
        target_lang = 'en'

    return locale_to_lower_upper(target_lang)


def setup_gettext(locale):
    """
    Setup the gettext instance based on this locale
    """
    # Later on when we have plugins we may want to enable the
    # multi-translations system they have so we can handle plugin
    # translations too

    # TODO: fallback nicely on translations from pt_PT to pt if not
    # available, etc.
    this_gettext = gettext.translation(
        'mediagoblin', TRANSLATIONS_PATH, [locale], fallback=True)

    mgoblin_globals.setup_globals(
        translations=this_gettext)
