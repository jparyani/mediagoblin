#!/bin/bash

# When you change this file, you must take manual action. Read this doc:
# - https://docs.sandstorm.io/en/latest/vagrant-spk/customizing/#setupsh

set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y nginx uwsgi uwsgi-plugin-python build-essential python-dev python-virtualenv git
apt-get install -y libxml2-dev libxslt1-dev python-dev
apt-get -y install python-lxml python-imaging
# apt-get -y install poppler-utils unoconv libreoffice
apt-get install -y libtiff5-dev libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python-tk
apt-get install -y python-numpy python-scipy

service nginx stop
systemctl disable nginx
