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

import gettext
import pkg_resources
from babel.localedata import exists
from babel.support import LazyProxy

from mediagoblin import mg_globals

###################
# Translation tools
###################


TRANSLATIONS_PATH = pkg_resources.resource_filename(
    'mediagoblin', 'i18n')


def locale_to_lower_upper(locale):
    """
    Take a locale, regardless of style, and format it like "en-US"
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
    Take a locale, regardless of style, and format it like "en_us"
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

    # Your routing can explicitly specify a target language
    matchdict = request.matchdict or {}

    if matchdict.has_key('locale'):
        target_lang = matchdict['locale']
    elif request.session.has_key('target_lang'):
        target_lang = request.session['target_lang']
    # Pull the first acceptable language or English
    else:
        # WebOb recently changed how it handles determining best language.
        # Here's a compromise commit that handles either/or...
        if hasattr(request.accept_language, "best_matches"):
            accept_lang_matches = request.accept_language.best_matches()
            if accept_lang_matches:
                target_lang = accept_lang_matches[0]
            else:
                target_lang = 'en'
        else:
            target_lang = request.accept.best_match(
                request.accept_language, 'en')

    return locale_to_lower_upper(target_lang)

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
    if locale in SETUP_GETTEXTS:
        this_gettext = SETUP_GETTEXTS[locale]
    else:
        this_gettext = gettext.translation(
            'mediagoblin', TRANSLATIONS_PATH, [locale], fallback=True)
        if exists(locale):
            SETUP_GETTEXTS[locale] = this_gettext

    mg_globals.thread_scope.translations = this_gettext


# Force en to be setup before anything else so that
# mg_globals.translations is never None
setup_gettext('en')


def pass_to_ugettext(*args, **kwargs):
    """
    Pass a translation on to the appropriate ugettext method.

    The reason we can't have a global ugettext method is because
    mg_globals gets swapped out by the application per-request.
    """
    return mg_globals.thread_scope.translations.ugettext(
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
    return mg_globals.thread_scope.translations.ngettext(
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
