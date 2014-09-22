import functools
import warnings

import six

if six.PY3:
    from email.mime.text import MIMEText
else:
    from email.MIMEText import MIMEText


def encode_to_utf8(method):
    def wrapper(self):
        if six.PY2 and isinstance(method(self), six.text_type):
            return method(self).encode('utf-8')
        return method(self)
    functools.update_wrapper(wrapper, method, ['__name__', '__doc__'])
    return wrapper


# based on django.utils.encoding.python_2_unicode_compatible
def py2_unicode(klass):
    if six.PY2:
        if '__str__' not in klass.__dict__:
            warnings.warn("@py2_unicode cannot be applied "
                          "to %s because it doesn't define __str__()." %
                          klass.__name__)
        klass.__unicode__ = klass.__str__
        klass.__str__ = encode_to_utf8(klass.__unicode__)
        if '__repr__' in klass.__dict__:
            klass.__repr__ = encode_to_utf8(klass.__repr__)
    return klass
