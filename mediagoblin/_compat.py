import sys

from six import PY3, iteritems

from mediagoblin import mg_globals

if PY3:
    from email.mime.text import MIMEText
    from urllib import parse as urlparse
    # TODO(berker): Rename to gettext and ungettext instead?
    ugettext = mg_globals.thread_scope.translations.gettext
    ungettext = mg_globals.thread_scope.translations.ngettext
else:
    from email.MIMEText import MIMEText
    import urlparse
    ugettext = mg_globals.thread_scope.translations.ugettext
    ungettext = mg_globals.thread_scope.translations.ungettext


def py2_unicode(klass):
    if not PY3:
        klass.__unicode__ = klass.__str__
        klass.__str__ = lambda self: self.__unicode__().encode('utf-8')
    return klass
