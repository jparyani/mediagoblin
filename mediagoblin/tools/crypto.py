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

import os.path
import logging
import random
import itsdangerous
from mediagoblin import mg_globals

_log = logging.getLogger(__name__)


# Use the system (hardware-based) random number generator if it exists.
# -- this optimization is lifted from Django
if hasattr(random, 'SystemRandom'):
    getrandbits = random.SystemRandom().getrandbits
else:
    getrandbits = random.getrandbits


__itsda_secret = None


def setup_crypto():
    global __itsda_secret
    dir = mg_globals.app_config["crypto_path"]
    if not os.path.isdir(dir):
        os.makedirs(dir)
        os.chmod(dir, 0700)
        _log.info("Created %s", dir)
    name = os.path.join(dir, "itsdangeroussecret.bin")
    if os.path.exists(name):
        __itsda_secret = file(name, "r").read()
    else:
        __itsda_secret = str(getrandbits(192))
        f = file(name, "w")
        f.write(__itsda_secret)
        f.close()
        os.chmod(name, 0600)
        _log.info("Created %s", name)


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
