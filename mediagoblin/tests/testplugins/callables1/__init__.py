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

from mediagoblin.tools.pluginapi import CantHandleIt

def setup_plugin():
    pass


def just_one(call_log):
    call_log.append("expect this one call")
    return "Called just once"


def multi_handle(call_log):
    call_log.append("Hi, I'm the first")
    return "the first returns"

def multi_handle_with_canthandle(call_log):
    raise CantHandleIt("I just can't accept this stupid method")


hooks = {
    'setup': setup_plugin,
    'just_one': just_one,
    'multi_handle': multi_handle,
    'multi_handle_with_canthandle': multi_handle_with_canthandle,
    }
