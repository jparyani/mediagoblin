#!/bin/bash

# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 Free Software Foundation, Inc
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


# usage: maketarball [-d] <rev-ish>
#
# Creates a tarball from a rev-ish.  If -d is passed in, then it adds
# the date to the directory name.
#
# Examples:
#
#    ./maketarball -d master
#    ./maketarball v0.0.2

if [[ -z "$1" ]]; then
    echo "Usage: $0 [-d] <rev-ish>";
    exit 1;
fi

NOWDATE=`date "+%Y-%m-%d"`

if [[ $@ == *-d* ]]; then
    REVISH=$2
    PREFIX="$NOWDATE-$REVISH"
else
    REVISH=$1
    PREFIX="$REVISH"
fi


# convert PREFIX to all lowercase.
# nix the v from tag names.
PREFIX=`echo "$PREFIX" | tr '[A-Z]' '[a-z]' | sed s/v//`

echo "== REVISH $REVISH"
echo "== PREFIX $PREFIX"

echo ""

echo "generating archive...."
git archive \
    --format=tar \
    --prefix=mediagoblin-$PREFIX/ \
    $REVISH > mediagoblin-$PREFIX.tar

if [[ $? -ne 0 ]]
then
    echo "git archive command failed.  See above text for reason."
    if [[ -e mediagoblin-$PREFIX.tar ]]
    then
        rm mediagoblin-$PREFIX.tar
    fi
    exit 1;
fi

echo "compressing...."
gzip mediagoblin-$PREFIX.tar

echo "archive at mediagoblin-$PREFIX.tar.gz"

echo "done."
