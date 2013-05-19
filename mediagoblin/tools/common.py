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

import sys


global TESTS_ENABLED
TESTS_ENABLED = False


def import_component(import_string):
    """
    Import a module component defined by STRING.  Probably a method,
    class, or global variable.

    Args:
     - import_string: a string that defines what to import.  Written
       in the format of "module1.module2:component"
    """
    module_name, func_name = import_string.split(':', 1)
    __import__(module_name)
    module = sys.modules[module_name]
    func = getattr(module, func_name)
    return func


def simple_printer(string):
    """
    Prints a string, but without an auto \n at the end.

    Useful for places where we want to dependency inject for printing.
    """
    sys.stdout.write(string)
    sys.stdout.flush()


class CollectingPrinter(object):
    """
    Another printer object, this one useful for capturing output for
    examination during testing or otherwise.

    Use this like:

      >>> printer = CollectingPrinter()
      >>> printer("herp derp\n")
      >>> printer("lollerskates\n")
      >>> printer.combined_string
      "herp derp\nlollerskates\n"
    """
    def __init__(self):
        self.collection = []
    
    def __call__(self, string):
        self.collection.append(string)

    @property
    def combined_string(self):
        return u''.join(self.collection)


