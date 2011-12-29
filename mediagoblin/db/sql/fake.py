"""
This module contains some fake classes and functions to
calm the rest of the code base. Or provide super minimal
implementations.

Currently:
- ObjectId "class": It's a function mostly doing
  int(init_arg) to convert string primary keys into
  integer primary keys.
- InvalidId exception
- DESCENDING "constant"
"""
    

DESCENDING = object()  # a unique object for this "constant"


class InvalidId(Exception):
    pass


def ObjectId(value=None):
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        raise InvalidId("%r is an invalid id" % value)
