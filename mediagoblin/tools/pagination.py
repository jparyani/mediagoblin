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

import urllib
import copy
from math import ceil, floor
from itertools import count
from werkzeug.datastructures import MultiDict

from six.moves import zip

PAGINATION_DEFAULT_PER_PAGE = 30


class Pagination(object):
    """
    Pagination class for database queries.

    Initialization through __init__(self, cursor, page=1, per_page=2),
    get actual data slice through __call__().
    """

    def __init__(self, page, cursor, per_page=PAGINATION_DEFAULT_PER_PAGE,
                 jump_to_id=False):
        """
        Initializes Pagination

        Args:
         - page: requested page
         - per_page: number of objects per page
         - cursor: db cursor
         - jump_to_id: object id, sets the page to the page containing the
           object with id == jump_to_id.
        """
        self.page = page
        self.per_page = per_page
        self.cursor = cursor
        self.total_count = self.cursor.count()
        self.active_id = None

        if jump_to_id:
            cursor = copy.copy(self.cursor)

            for (doc, increment) in list(zip(cursor, count(0))):
                if doc.id == jump_to_id:
                    self.page = 1 + int(floor(increment / self.per_page))

                    self.active_id = jump_to_id
                    break

    def __call__(self):
        """
        Returns slice of objects for the requested page
        """
        # TODO, return None for out of index so templates can
        # distinguish between empty galleries and out-of-bound pages???
        return self.cursor.slice(
            (self.page - 1) * self.per_page,
            self.page * self.per_page)

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

    def get_page_url_explicit(self, base_url, get_params, page_no):
        """
        Get a page url by adding a page= parameter to the base url
        """
        if isinstance(get_params, MultiDict):
            new_get_params = get_params.to_dict()
        else:
            new_get_params = dict(get_params) or {}

        new_get_params['page'] = page_no
        return "%s?%s" % (
            base_url, urllib.urlencode(new_get_params))

    def get_page_url(self, request, page_no):
        """
        Get a new page url based of the request, and the new page number.

        This is a nice wrapper around get_page_url_explicit()
        """
        return self.get_page_url_explicit(
            request.full_path, request.GET, page_no)
