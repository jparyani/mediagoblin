#!/bin/sh

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

#
# This runs Mediagoblin using Paste with Celery set to always eager mode.
# 

if [ "$1" = "-h" ]
then
    echo "$0 [-h] [-c paste.ini] [ARGS_to_paster ...]"
    echo ""
    echo "   For example:"
    echo "         $0 -c fcgi.ini port_number=23371"
    echo "     or: $0 --server-name=fcgi"
    echo ""
    echo "   The configfile defaults to paste_local.ini,"
    echo "   if that is readable, otherwise paste.ini."
    exit 1
fi

PASTE_INI=paste.ini

if [ -r paste_local.ini ]
then
    PASTE_INI=paste_local.ini
fi

if [ "$1" = "-c" ]
then
    PASTE_INI="$2"
    shift
    shift
fi

echo "Using paste config: $PASTE_INI"

if [ -f ./bin/paster ]; then
    echo "Using ./bin/paster";
    export PASTER="./bin/paster";
elif which paster > /dev/null; then
    echo "Using paster from \$PATH";
    export PASTER="paster";
else
    echo "No paster found, exiting! X_X";
    exit 1
fi

set -x
CELERY_ALWAYS_EAGER=true $PASTER serve $PASTE_INI "$@" --reload
