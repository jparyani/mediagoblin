import sys

from six import PY3, iteritems

if PY3:
    from email.mime.text import MIMEText
    from urllib import parse as urlparse
else:
    from email.MIMEText import MIMEText
    import urlparse
