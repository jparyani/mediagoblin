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
./bin/tx pull -a

git add mediagoblin/i18n/
git commit -m "Committing present MediaGoblin translations before pushing extracted messages" \
    || true  # Don't fail if nothing to commit

echo "==> Extracting translations"
./bin/pybabel extract -F babel.ini -o mediagoblin/i18n/en/LC_MESSAGES/mediagoblin.po .

echo "==> Pushing extracted translations to Transifex"
./bin/tx push -s

echo "==> Waiting 5 seconds, so the server can process the new stuff (hopefully)"
sleep 5

# gets the new strings added to all files
echo "==> Re-Pulling translations from Transifex"
./bin/tx pull -a

echo "==> Compiling .mo files"
./bin/pybabel compile -D mediagoblin -d mediagoblin/i18n/

echo "==> Committing to git"
git add mediagoblin/i18n/

git commit -m "Committing extracted and compiled translations" || true

echo "... done.  Now consider pushing up those commits!"
