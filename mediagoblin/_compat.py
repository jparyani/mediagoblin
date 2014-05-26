import sys

from six import PY3, iteritems

from mediagoblin import mg_globals

if PY3:
    from email.mime.text import MIMEText
    from urllib import parse as urlparse
    ugettext = mg_globals.thread_scope.translations.gettext
    ungettext = mg_globals.thread_scope.translations.ngettext
else:
    from email.MIMEText import MIMEText
    import urlparse
    ugettext = mg_globals.thread_scope.translations.ugettext
    ungettext = mg_globals.thread_scope.translations.ungettext
