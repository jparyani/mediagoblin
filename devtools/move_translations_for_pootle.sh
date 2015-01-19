#!/bin/bash

# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 GNU MediaGoblin contributors.  See AUTHORS.
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

# exit if anything fails
set -e

# move the files to Pootle-friendly layout
for lang in $(ls mediagoblin/i18n/); do
	from="mediagoblin/i18n/$lang/LC_MESSAGES/mediagoblin.po"
	to="mediagoblin/i18n/$lang/mediagoblin.po"
	git mv $from $to
done

# english is not required and is Pootle's "template" now
mkdir mediagoblin/i18n/templates/
git mv mediagoblin/i18n/en/mediagoblin.po \
	mediagoblin/i18n/templates/mediagoblin.pot
