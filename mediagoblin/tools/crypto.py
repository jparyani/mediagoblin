# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2013 MediaGoblin contributors.  See AUTHORS.
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

import base64
import string
import errno
import itsdangerous
import logging
import os.path
import random
import tempfile
from mediagoblin import mg_globals

_log = logging.getLogger(__name__)

# produces base64 alphabet
ALPHABET = string.ascii_letters + "-_"

# Use the system (hardware-based) random number generator if it exists.
# -- this optimization is lifted from Django
try:
    getrandbits = random.SystemRandom().getrandbits
except AttributeError:
    getrandbits = random.getrandbits

# TODO: This should be attached to the MediaGoblinApp
__itsda_secret = None


def load_key(filename):
    global __itsda_secret
    key_file = open(filename)
    try:
        __itsda_secret = key_file.read()
    finally:
        key_file.close()


def create_key(key_dir, key_filepath):
    global __itsda_secret
    old_umask = os.umask(0o77)
    key_file = None
    try:
        if not os.path.isdir(key_dir):
            os.makedirs(key_dir)
            _log.info("Created %s", key_dir)
        key = str(getrandbits(192))
        key_file = tempfile.NamedTemporaryFile(dir=key_dir, suffix='.bin',
                                               delete=False)
        key_file.write(key.encode('ascii'))
        key_file.flush()
        os.rename(key_file.name, key_filepath)
        key_file.close()
    finally:
        os.umask(old_umask)
        if (key_file is not None) and (not key_file.closed):
            key_file.close()
            os.unlink(key_file.name)
    __itsda_secret = key
    _log.info("Saved new key for It's Dangerous")


def setup_crypto(app_config):
    global __itsda_secret
    key_dir = app_config["crypto_path"]
    key_filepath = os.path.join(key_dir, 'itsdangeroussecret.bin')
    try:
        load_key(key_filepath)
    except IOError as error:
        if error.errno != errno.ENOENT:
            raise
        create_key(key_dir, key_filepath)


def get_timed_signer_url(namespace):
    """
    This gives a basic signing/verifying object.

    The namespace makes sure signed tokens can't be used in
    a different area. Like using a forgot-password-token as
    a session cookie.

    Basic usage:

    .. code-block:: python

       _signer = None
       TOKEN_VALID_DAYS = 10
       def setup():
           global _signer
           _signer = get_timed_signer_url("session cookie")
       def create_token(obj):
           return _signer.dumps(obj)
       def parse_token(token):
           # This might raise an exception in case
           # of an invalid token, or an expired token.
           return _signer.loads(token, max_age=TOKEN_VALID_DAYS*24*3600)

    For more details see
    http://pythonhosted.org/itsdangerous/#itsdangerous.URLSafeTimedSerializer
    """
    assert __itsda_secret is not None
    return itsdangerous.URLSafeTimedSerializer(__itsda_secret,
         salt=namespace)

def random_string(length, alphabet=ALPHABET):
    """ Returns a URL safe base64 encoded crypographically strong string """
    base = len(alphabet)
    rstring = ""
    for i in range(length):
        n = getrandbits(6) # 6 bytes = 2^6 = 64
        n = divmod(n, base)[1]
        rstring += alphabet[n]

    return rstring
