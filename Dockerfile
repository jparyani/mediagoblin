# Use phusion/baseimage as base image. To make your builds reproducible, make
# sure you lock down to a specific version, not to `latest`!
# See https://github.com/phusion/baseimage-docker/blob/master/Changelog.md for
# a list of version numbers.
FROM phusion/baseimage:0.9.16

# Set correct environment variables.
ENV HOME /root

# Disable SSH
RUN rm -rf /etc/service/sshd /etc/my_init.d/00_regen_ssh_host_keys.sh
# Disable cron
RUN rm -rf /etc/service/cron

# Use baseimage-docker's init system.
CMD ["/sbin/my_init"]

RUN apt-get update
RUN apt-get -y install software-properties-common

# install mediagoblin dependencies
RUN apt-get -y install git-core python python-dev python-lxml python-imaging python-virtualenv

# install document dependencies
RUN apt-get -y install poppler-utils unoconv libreoffice

# install gstreamer and other audio/video dependencies
RUN apt-get -y install python-gst0.10  gstreamer0.10-plugins-base gstreamer0.10-plugins-bad gstreamer0.10-plugins-good gstreamer0.10-plugins-ugly python-numpy python-scipy libsndfile1-dev
RUN add-apt-repository ppa:mc3man/trusty-media
RUN apt-get update
RUN apt-get -y install gstreamer0.10-ffmpeg

# setup app to run as a service
RUN mkdir /etc/service/app
ADD app.sh /etc/service/app/run

ADD ./requirements.txt /tmp/requirements.txt
RUN mkdir -p /opt/app && cd /opt/app && (virtualenv --system-site-packages . || virtualenv .) && ./bin/pip install -r /tmp/requirements.txt
RUN /opt/app/bin/pip install scikits.audiolab
RUN mv /opt/app /tmp/virtualenv

ADD . /opt/app
RUN cd /opt/app && cp -r /tmp/virtualenv/* .

RUN cd /opt/app && ./bin/python setup.py develop
RUN mkdir -p /var/user_dev/media/public/media_entries && mkdir -p /var/user_dev/media/queue/media_entries
RUN cd /opt/app && ./bin/gmg dbupdate
RUN mkdir -p /var/user_dev && ln -s /var/user_dev /opt/app

EXPOSE 6543

# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN rm -rf /usr/share/vim /usr/share/doc /usr/share/man /var/lib/dpkg /var/lib/belocs /var/lib/ucf /var/cache/debconf /var/log/*.log
