# Use phusion/baseimage as base image. To make your builds reproducible, make
# sure you lock down to a specific version, not to `latest`!
# See https://github.com/phusion/baseimage-docker/blob/master/Changelog.md for
# a list of version numbers.
FROM phusion/baseimage:0.9.10

# Set correct environment variables.
ENV HOME /root

# Disable SSH
RUN rm -rf /etc/service/sshd /etc/my_init.d/00_regen_ssh_host_keys.sh
# Disable cron
RUN rm -rf /etc/service/cron

# Use baseimage-docker's init system.
CMD ["/sbin/my_init"]

RUN apt-get update

# Install python
RUN apt-get -y install python

# install mediagoblin dependencies
RUN apt-get -y install git-core python python-dev python-lxml python-imaging python-virtualenv

RUN mkdir /etc/service/app
ADD app.sh /etc/service/app/run

ADD . /opt/app
RUN rm -rf /opt/app/.git
RUN cd /opt/app && (virtualenv --system-site-packages . || virtualenv .) && ./bin/python setup.py develop
RUN mkdir -p /var/user_dev/media/public && mkdir -p /var/user_dev/media/queue

EXPOSE 33411

# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN rm -rf /usr/share/vim /usr/share/doc /usr/share/man /var/lib/dpkg /var/lib/belocs /var/lib/ucf /var/cache/debconf /var/log/*.log