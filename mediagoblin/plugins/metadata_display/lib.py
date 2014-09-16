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

def rdfa_to_readable(rdfa_predicate):
    """
    A simple script to convert rdfa resource descriptors into a form more
    accessible for humans.
    """
    components = rdfa_predicate.split(u":")
    if len(components) >= 2:
        readable = components[1].capitalize()
    else:
        readable = u""
    return readable

def add_rdfa_to_readable_to_media_home(context):
    """
    A context hook which adds the 'rdfa_to_readable' filter to
    the media home page.
    """
    context['rdfa_to_readable'] = rdfa_to_readable
    return context
