from six import PY3

if PY3:
    from email.mime.text import MIMEText
else:
    from email.MIMEText import MIMEText


# taken from
# https://github.com/django/django/blob/master/django/utils/encoding.py
def py2_unicode(klass):
    # TODO: Add support for __repr__
    if not PY3:
        if '__str__' not in klass.__dict__:
            raise ValueError("@py2_unicode cannot be applied "
                             "to %s because it doesn't define __str__()." %
                             klass.__name__)
        klass.__unicode__ = klass.__str__
        klass.__str__ = lambda self: self.__unicode__().encode('utf-8')
    return klass
