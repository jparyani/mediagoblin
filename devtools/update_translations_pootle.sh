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

echo "==> checking out master"
git checkout master

echo "==> pulling git master"
git pull

echo "==> pulling present translations"
rsync -vaz chapters.gnu.org::pootle/mediagoblin/ mediagoblin/i18n/

echo "==> Extracting translations"
./bin/pybabel extract -F babel.ini -o mediagoblin/i18n/templates/mediagoblin.pot .

echo "==> Compiling .mo files"
./bin/pybabel compile -D mediagoblin -d mediagoblin/i18n/

echo "==> Committing to git"
git add mediagoblin/i18n/

git commit -m "Committing extracted and compiled translations" || true

echo "... done.  Now consider pushing up those commits!"
