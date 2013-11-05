#!/bin/bash

# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 GNU MediaGoblin Contributors.  See AUTHORS.
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

USAGE="Usage: $0 -h | [-p PATH] -e ENVIRONMENT"

ENVIRONMENT="migration-18"
USER_DEV="user_dev_default"
DEV_ENV_DIRECTORY_PATH="../mg-dev-environments"

while getopts ":hp:e:" opt;
do
    case $opt in
        h)
            echo $USAGE
            echo "Sets up an example mediagoblin instance for testing code."
            echo ""
            echo "    -h                Shows this help message."
            echo "    -p=PATH           The path to your mg-dev-environments repository"
            echo "    -e=ENVIRONMENT    The name of the environment you want to set up. Useful"
            echo "                      if you want to set up a database from a past version."
            echo "                      This defaults to a database from the most recent version"
            echo "                      of master."
            exit 1
            ;;
        e)
            ENVIRONMENT=$OPTARG
            ;;
        p)
            DEV_ENV_DIRECTORY_PATH=$OPTARG
            ;;
        \?)
            echo "Invalid Option: -$OPTARG" >&2
            ;;
        :)
            echo "Option -$OPTARG requires an argument" >&2
            ;;
    esac
done

if [ ! -d $DEV_ENV_DIRECTORY_PATH ]; then
    echo "$DEV_ENV_DIRECTORY_PATH not found. Have you downloaded the repo from \
git@gitorious.org:mediagoblin/mg-dev-environments.git ?" >&2
    echo ""
    exit 1
fi

if [ ! -d "user_dev" ]; then
    echo "ERROR: This script should be executed from within your mediagoblin \
instance directory" >&2
    exit 1
fi

if [ ! -e "$DEV_ENV_DIRECTORY_PATH/$ENVIRONMENT.tar.gz" ]; then
    echo "$ENVIRONMENT.tar.gz not found in directory $DEV_ENV_DIRECTORY_PATH" >&2
    exit 1
else
    echo "***WARNING!***"
    echo "This script will WIPE YOUR FULL CURRENT ENVIRONMENT and REPLACE IT with a test database and media!"
    echo "Your databases and user_dev/ will all likely be wiped!"
    echo -n "Do you want to continue? (y/n) "
    read -n1 USER_CONFIRM
    echo ""
    counter=0
    while [ "$USER_CONFIRM"=="y" ]; do
        case $USER_CONFIRM in
            y)
                break
                ;;
            n)
                exit 1
                ;;
            *)
                if [ $counter -lt 5 ]; then
                    echo "Invalid option. Please enter 'y' or 'n'"
                    echo "Do you want to continue? (y/n)"
                    read -n1 USER_CONFIRM
                    echo ""
                    counter+=1
                    continue
                else
                    exit 1
                fi
                ;;
        esac
    done
    tar -xzf $DEV_ENV_DIRECTORY_PATH/$ENVIRONMENT.tar.gz
    tar -xzf $DEV_ENV_DIRECTORY_PATH/$USER_DEV.tar.gz
    echo "Completed."
    exit 0
fi
