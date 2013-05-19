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

import re
# This import *is* used; see word.encode('tranlit/long') below.
from unicodedata import normalize

try:
    import translitcodec
    USING_TRANSLITCODEC = True
except ImportError:
    USING_TRANSLITCODEC = False


_punct_re = re.compile(r'[\t !"#:$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


def slugify(text, delim=u'-'):
    """
    Generates an ASCII-only slug. Taken from http://flask.pocoo.org/snippets/5/
    """
    result = []
    for word in _punct_re.split(text.lower()):
        if USING_TRANSLITCODEC:
            word = word.encode('translit/long')
        else:
            word = normalize('NFKD', word).encode('ascii', 'ignore')

        if word:
            result.append(word)
    return unicode(delim.join(result))
