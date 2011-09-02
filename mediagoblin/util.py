# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 MediaGoblin contributors.  See AUTHORS.
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

from __future__ import division

from email.MIMEText import MIMEText
import gettext
import pkg_resources
import smtplib
import sys
import re
import urllib
from math import ceil, floor
import copy
import wtforms

from babel.localedata import exists
from babel.support import LazyProxy
import jinja2
import translitcodec
from webob import Response, exc
from lxml.html.clean import Cleaner
import markdown
from wtforms.form import Form

from mediagoblin import mg_globals
from mediagoblin import messages
from mediagoblin.db.util import ObjectId

from itertools import izip, count

DISPLAY_IMAGE_FETCHING_ORDER = [u'medium', u'original', u'thumb']

TESTS_ENABLED = False
def _activate_testing():
    """
    Call this to activate testing in util.py
    """
    global TESTS_ENABLED
    TESTS_ENABLED = True


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


SETUP_JINJA_ENVS = {}


def get_jinja_env(template_loader, locale):
    """
    Set up the Jinja environment, 

    (In the future we may have another system for providing theming;
    for now this is good enough.)
    """
    setup_gettext(locale)

    # If we have a jinja environment set up with this locale, just
    # return that one.
    if SETUP_JINJA_ENVS.has_key(locale):
        return SETUP_JINJA_ENVS[locale]

    template_env = jinja2.Environment(
        loader=template_loader, autoescape=True,
        extensions=['jinja2.ext.i18n', 'jinja2.ext.autoescape'])

    template_env.install_gettext_callables(
        mg_globals.translations.ugettext,
        mg_globals.translations.ungettext)

    # All templates will know how to ...
    # ... fetch all waiting messages and remove them from the queue
    # ... construct a grid of thumbnails or other media
    template_env.globals['fetch_messages'] = messages.fetch_messages
    template_env.globals['gridify_list'] = gridify_list
    template_env.globals['gridify_cursor'] = gridify_cursor

    if exists(locale):
        SETUP_JINJA_ENVS[locale] = template_env

    return template_env


# We'll store context information here when doing unit tests
TEMPLATE_TEST_CONTEXT = {}


def render_template(request, template_path, context):
    """
    Render a template with context.

    Always inserts the request into the context, so you don't have to.
    Also stores the context if we're doing unit tests.  Helpful!
    """
    template = request.template_env.get_template(
        template_path)
    context['request'] = request
    rendered = template.render(context)

    if TESTS_ENABLED:
        TEMPLATE_TEST_CONTEXT[template_path] = context

    return rendered


def clear_test_template_context():
    global TEMPLATE_TEST_CONTEXT
    TEMPLATE_TEST_CONTEXT = {}


def render_to_response(request, template, context, status=200):
    """Much like Django's shortcut.render()"""
    return Response(
        render_template(request, template, context),
        status=status)


def redirect(request, *args, **kwargs):
    """Returns a HTTPFound(), takes a request and then urlgen params"""
    
    querystring = None
    if kwargs.get('querystring'):
        querystring = kwargs.get('querystring')
        del kwargs['querystring']

    return exc.HTTPFound(
        location=''.join([
                request.urlgen(*args, **kwargs),
                querystring if querystring else '']))


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
        {'_id': ObjectId(request.session['user_id'])})

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

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

def slugify(text, delim=u'-'):
    """
    Generates an ASCII-only slug. Taken from http://flask.pocoo.org/snippets/5/
    """
    result = []
    for word in _punct_re.split(text.lower()):
        word = word.encode('translit/long')
        if word:
            result.append(word)
    return unicode(delim.join(result))

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
    if TESTS_ENABLED or mg_globals.app_config['email_debug_mode']:
        mhost = FakeMhost()
    elif not mg_globals.app_config['email_debug_mode']:
        mhost = smtplib.SMTP(
            mg_globals.app_config['email_smtp_host'],
            mg_globals.app_config['email_smtp_port'])

        # SMTP.__init__ Issues SMTP.connect implicitly if host
        if not mg_globals.app_config['email_smtp_host']:  # e.g. host = ''
            mhost.connect()  # We SMTP.connect explicitly

    if mg_globals.app_config['email_smtp_user'] \
            or mg_globals.app_config['email_smtp_pass']:
        mhost.login(
            mg_globals.app_config['email_smtp_user'],
            mg_globals.app_config['email_smtp_pass'])

    message = MIMEText(message_body.encode('utf-8'), 'plain', 'utf-8')
    message['Subject'] = subject
    message['From'] = from_addr
    message['To'] = ', '.join(to_addrs)

    if TESTS_ENABLED:
        EMAIL_TEST_INBOX.append(message)

    if mg_globals.app_config['email_debug_mode']:
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
    'mediagoblin', 'i18n')


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
    matchdict = request.matchdict or {}

    if matchdict.has_key('locale'):
        target_lang = matchdict['locale']
    elif request.session.has_key('target_lang'):
        target_lang = request.session['target_lang']
    # Pull the first acceptable language
    elif accept_lang_matches:
        target_lang = accept_lang_matches[0]
    # Fall back to English
    else:
        target_lang = 'en'

    return locale_to_lower_upper(target_lang)


# A super strict version of the lxml.html cleaner class
HTML_CLEANER = Cleaner(
    scripts=True,
    javascript=True,
    comments=True,
    style=True,
    links=True,
    page_structure=True,
    processing_instructions=True,
    embedded=True,
    frames=True,
    forms=True,
    annoying_tags=True,
    allow_tags=[
        'div', 'b', 'i', 'em', 'strong', 'p', 'ul', 'ol', 'li', 'a', 'br'],
    remove_unknown_tags=False, # can't be used with allow_tags
    safe_attrs_only=True,
    add_nofollow=True, # for now
    host_whitelist=(),
    whitelist_tags=set([]))


def clean_html(html):
    # clean_html barfs on an empty string
    if not html:
        return u''

    return HTML_CLEANER.clean_html(html)


def convert_to_tag_list_of_dicts(tag_string):
    """
    Filter input from incoming string containing user tags,

    Strips trailing, leading, and internal whitespace, and also converts
    the "tags" text into an array of tags
    """
    taglist = []
    if tag_string:

        # Strip out internal, trailing, and leading whitespace
        stripped_tag_string = u' '.join(tag_string.strip().split())

        # Split the tag string into a list of tags
        for tag in stripped_tag_string.split(
                                       mg_globals.app_config['tags_delimiter']):

            # Ignore empty or duplicate tags
            if tag.strip() and tag.strip() not in [t['name'] for t in taglist]:

                taglist.append({'name': tag.strip(),
                                'slug': slugify(tag.strip())})
    return taglist


def media_tags_as_string(media_entry_tags):
    """
    Generate a string from a media item's tags, stored as a list of dicts

    This is the opposite of convert_to_tag_list_of_dicts
    """
    media_tag_string = ''
    if media_entry_tags:
        media_tag_string = mg_globals.app_config['tags_delimiter'].join(
                                      [tag['name'] for tag in media_entry_tags])
    return media_tag_string

TOO_LONG_TAG_WARNING = \
    u'Tags must be shorter than %s characters.  Tags that are too long: %s'

def tag_length_validator(form, field):
    """
    Make sure tags do not exceed the maximum tag length.
    """
    tags = convert_to_tag_list_of_dicts(field.data)
    too_long_tags = [
        tag['name'] for tag in tags
        if len(tag['name']) > mg_globals.app_config['tags_max_length']]

    if too_long_tags:
        raise wtforms.ValidationError(
            TOO_LONG_TAG_WARNING % (mg_globals.app_config['tags_max_length'], \
                                    ', '.join(too_long_tags)))


MARKDOWN_INSTANCE = markdown.Markdown(safe_mode='escape')

def cleaned_markdown_conversion(text):
    """
    Take a block of text, run it through MarkDown, and clean its HTML.
    """
    # Markdown will do nothing with and clean_html can do nothing with
    # an empty string :)
    if not text:
        return u''

    return clean_html(MARKDOWN_INSTANCE.convert(text))


SETUP_GETTEXTS = {}

def setup_gettext(locale):
    """
    Setup the gettext instance based on this locale
    """
    # Later on when we have plugins we may want to enable the
    # multi-translations system they have so we can handle plugin
    # translations too

    # TODO: fallback nicely on translations from pt_PT to pt if not
    # available, etc.
    if SETUP_GETTEXTS.has_key(locale):
        this_gettext = SETUP_GETTEXTS[locale]
    else:
        this_gettext = gettext.translation(
            'mediagoblin', TRANSLATIONS_PATH, [locale], fallback=True)
        if exists(locale):
            SETUP_GETTEXTS[locale] = this_gettext

    mg_globals.setup_globals(
        translations=this_gettext)


# Force en to be setup before anything else so that
# mg_globals.translations is never None
setup_gettext('en')


def pass_to_ugettext(*args, **kwargs):
    """
    Pass a translation on to the appropriate ugettext method.

    The reason we can't have a global ugettext method is because
    mg_globals gets swapped out by the application per-request.
    """
    return mg_globals.translations.ugettext(
        *args, **kwargs)


def lazy_pass_to_ugettext(*args, **kwargs):
    """
    Lazily pass to ugettext.

    This is useful if you have to define a translation on a module
    level but you need it to not translate until the time that it's
    used as a string.
    """
    return LazyProxy(pass_to_ugettext, *args, **kwargs)


def pass_to_ngettext(*args, **kwargs):
    """
    Pass a translation on to the appropriate ngettext method.

    The reason we can't have a global ngettext method is because
    mg_globals gets swapped out by the application per-request.
    """
    return mg_globals.translations.ngettext(
        *args, **kwargs)


def lazy_pass_to_ngettext(*args, **kwargs):
    """
    Lazily pass to ngettext.

    This is useful if you have to define a translation on a module
    level but you need it to not translate until the time that it's
    used as a string.
    """
    return LazyProxy(pass_to_ngettext, *args, **kwargs)


def fake_ugettext_passthrough(string):
    """
    Fake a ugettext call for extraction's sake ;)

    In wtforms there's a separate way to define a method to translate
    things... so we just need to mark up the text so that it can be
    extracted, not so that it's actually run through gettext.
    """
    return string


PAGINATION_DEFAULT_PER_PAGE = 30

class Pagination(object):
    """
    Pagination class for mongodb queries.

    Initialization through __init__(self, cursor, page=1, per_page=2),
    get actual data slice through __call__().
    """

    def __init__(self, page, cursor, per_page=PAGINATION_DEFAULT_PER_PAGE,
                 jump_to_id=False):
        """
        Initializes Pagination

        Args:
         - page: requested page
         - per_page: number of objects per page
         - cursor: db cursor 
         - jump_to_id: ObjectId, sets the page to the page containing the object
           with _id == jump_to_id.
        """
        self.page = page
        self.per_page = per_page
        self.cursor = cursor
        self.total_count = self.cursor.count()
        self.active_id = None

        if jump_to_id:
            cursor = copy.copy(self.cursor)

            for (doc, increment) in izip(cursor, count(0)):
                if doc['_id'] == jump_to_id:
                    self.page = 1 + int(floor(increment / self.per_page))

                    self.active_id = jump_to_id
                    break


    def __call__(self):
        """
        Returns slice of objects for the requested page
        """
        return self.cursor.skip(
            (self.page - 1) * self.per_page).limit(self.per_page)

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

    def get_page_url_explicit(self, base_url, get_params, page_no):
        """ 
        Get a page url by adding a page= parameter to the base url
        """ 
        new_get_params = copy.copy(get_params or {})
        new_get_params['page'] = page_no
        return "%s?%s" % (
            base_url, urllib.urlencode(new_get_params))

    def get_page_url(self, request, page_no):
        """ 
        Get a new page url based of the request, and the new page number.

        This is a nice wrapper around get_page_url_explicit()
        """ 
        return self.get_page_url_explicit(
            request.path_info, request.GET, page_no)


def gridify_list(this_list, num_cols=5):
    """
    Generates a list of lists where each sub-list's length depends on
    the number of columns in the list
    """
    grid = []

    # Figure out how many rows we should have
    num_rows = int(ceil(float(len(this_list)) / num_cols))

    for row_num in range(num_rows):
        slice_min = row_num * num_cols
        slice_max = (row_num + 1) * num_cols

        row = this_list[slice_min:slice_max]

        grid.append(row)

    return grid


def gridify_cursor(this_cursor, num_cols=5):
    """
    Generates a list of lists where each sub-list's length depends on
    the number of columns in the list
    """
    return gridify_list(list(this_cursor), num_cols)


def render_404(request):
    """
    Render a 404.
    """
    return render_to_response(
        request, 'mediagoblin/404.html', {}, status=400)

def delete_media_files(media):
    """
    Delete all files associated with a MediaEntry

    Arguments:
     - media: A MediaEntry document
    """
    for handle, listpath in media['media_files'].items():
        mg_globals.public_store.delete_file(
            listpath)

    for attachment in media['attachment_files']:
        mg_globals.public_store.delete_file(
            attachment['filepath'])
