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


from babel import localedata
from babel.support import LazyProxy

from mediagoblin import mg_globals

###################
# Translation tools
###################

AVAILABLE_LOCALES = None
TRANSLATIONS_PATH = pkg_resources.resource_filename(
    'mediagoblin', 'i18n')


def set_available_locales():
    """Set available locales for which we have translations"""
    global AVAILABLE_LOCALES
    locales=['en', 'en_US'] # these are available without translations
    for locale in localedata.list():
        if gettext.find('mediagoblin', TRANSLATIONS_PATH, [locale]):
            locales.append(locale)
    AVAILABLE_LOCALES = locales


def locale_to_lower_upper(locale):
    """
    Take a locale, regardless of style, and format it like "en_US"
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
    Return most appropriate language based on prefs/request request
    """
    request_args = (request.args, request.form)[request.method=='POST']

    if 'lang' in request_args:
        # User explicitely demanded a language, normalize lower_uppercase
        target_lang = locale_to_lower_upper(request_args['lang'])

    elif 'target_lang' in request.session:
        # TODO: Uh, ohh, this is never ever set anywhere?
        target_lang = request.session['target_lang']
    else:
        # Pull the most acceptable language based on browser preferences
        # This returns one of AVAILABLE_LOCALES which is aready case-normalized.
        # Note: in our tests request.accept_languages is None, so we need
        # to explicitely fallback to en here.
        target_lang = request.accept_languages.best_match(AVAILABLE_LOCALES) \
                      or "en_US"

    return target_lang

SETUP_GETTEXTS = {}

def get_gettext_translation(locale):
    """
    Return the gettext instance based on this locale
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
        if localedata.exists(locale):
            SETUP_GETTEXTS[locale] = this_gettext
    return this_gettext


def pass_to_ugettext(*args, **kwargs):
    """
    Pass a translation on to the appropriate ugettext method.

    The reason we can't have a global ugettext method is because
    mg_globals gets swapped out by the application per-request.
    """
    return mg_globals.thread_scope.translations.ugettext(
        *args, **kwargs)


def pass_to_ungettext(*args, **kwargs):
    """
    Pass a translation on to the appropriate ungettext method.

    The reason we can't have a global ugettext method is because
    mg_globals gets swapped out by the application per-request.
    """
    return mg_globals.thread_scope.translations.ungettext(
        *args, **kwargs)

def lazy_pass_to_ugettext(*args, **kwargs):
    """
    Lazily pass to ugettext.

    This is useful if you have to define a translation on a module
    level but you need it to not translate until the time that it's
    used as a string. For example, in:
        def func(self, message=_('Hello boys and girls'))

    you would want to use the lazy version for _.
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

def lazy_pass_to_ungettext(*args, **kwargs):
    """
    Lazily pass to ungettext.

    This is useful if you have to define a translation on a module
    level but you need it to not translate until the time that it's
    used as a string.
    """
    return LazyProxy(pass_to_ungettext, *args, **kwargs)


def fake_ugettext_passthrough(string):
    """
    Fake a ugettext call for extraction's sake ;)

    In wtforms there's a separate way to define a method to translate
    things... so we just need to mark up the text so that it can be
    extracted, not so that it's actually run through gettext.
    """
    return string
