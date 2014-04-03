.. MediaGoblin Documentation

   Written in 2011, 2012, 2013 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

.. _deploying-chapter:

=====================
Deploying MediaGoblin
=====================

GNU MediaGoblin is fairly new and so at the time of writing, there
aren't easy package-manager-friendly methods to install MediaGoblin.
However, doing a basic install isn't too complex in and of itself.

There's an almost infinite way to deploy things... for now, we'll keep
it simple with some assumptions and use a setup that combines
mediagoblin + virtualenv + fastcgi + nginx on a .deb or .rpm based
GNU/Linux distro.

.. note::

   These tools are for site administrators wanting to deploy a fresh
   install.  If instead you want to join in as a contributor, see our
   `Hacking HOWTO <http://wiki.mediagoblin.org/HackingHowto>`_ instead.

   There are also many ways to install servers... for the sake of
   simplicity, our instructions below describe installing with nginx.
   For more recipes, including Apache, see
   `our wiki <http://wiki.mediagoblin.org/Deployment>`_.

Prepare System
--------------

Dependencies
~~~~~~~~~~~~

MediaGoblin has the following core dependencies:

- Python 2.6 or 2.7
- `python-lxml <http://lxml.de/>`_
- `git <http://git-scm.com/>`_
- `SQLite <http://www.sqlite.org/>`_/`PostgreSQL <http://www.postgresql.org/>`_
- `Python Imaging Library <http://www.pythonware.com/products/pil/>`_  (PIL)
- `virtualenv <http://www.virtualenv.org/>`_

On a DEB-based system (e.g Debian, gNewSense, Trisquel, Ubuntu, and
derivatives) issue the following command::

    sudo apt-get install git-core python python-dev python-lxml \
        python-imaging python-virtualenv

On a RPM-based system (e.g. Fedora, RedHat, and derivatives) issue the
following command::

    yum install python-paste-deploy python-paste-script \
        git-core python python-devel python-lxml python-imaging \
        python-virtualenv

Configure PostgreSQL
~~~~~~~~~~~~~~~~~~~~

.. note::

   MediaGoblin currently supports PostgreSQL and SQLite. The default is a
   local SQLite database. This will "just work" for small deployments.

   For medium to large deployments we recommend PostgreSQL.

   If you don't want/need postgres, skip this section.

These are the packages needed for Debian Wheezy (stable)::

    sudo apt-get install postgresql postgresql-client python-psycopg2

The installation process will create a new *system* user named ``postgres``,
it will have privilegies sufficient to manage the database. We will create a
new database user with restricted privilegies and a new database owned by our
restricted database user for our MediaGoblin instance.

In this example, the database user will be ``mediagoblin`` and the database
name will be ``mediagoblin`` too.

To create our new user, run::

    sudo -u postgres createuser -A -D mediagoblin

then create the database all our MediaGoblin data should be stored in::

    sudo -u postgres createdb -E UNICODE -O mediagoblin mediagoblin

where the first ``mediagoblin`` is the database owner and the second
``mediagoblin`` is the database name.

.. caution:: Where is the password?

    These steps enable you to authenticate to the database in a password-less
    manner via local UNIX authentication provided you run the MediaGoblin
    application as a user with the same name as the user you created in
    PostgreSQL.

    More on this in :ref:`Drop Privileges for MediaGoblin <drop-privileges-for-mediagoblin>`.


.. _drop-privileges-for-mediagoblin:

Drop Privileges for MediaGoblin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MediaGoblin does not require special permissions or elevated
access to run. As such, the preferred way to run MediaGoblin is to
create a dedicated, unprivileged system user for the sole purpose of running
MediaGoblin. Running MediaGoblin processes under an unpriviledged system user
helps to keep it more secure. 

The following command (entered as root or with sudo) will create a
system account with a username of ``mediagoblin``. You may choose a different
username if you wish.::

   adduser --system mediagoblin

No password will be assigned to this account, and you will not be able
to log in as this user. To switch to this account, enter either::

  sudo -u mediagoblin /bin/bash  # (if you have sudo permissions)

or::

  su mediagoblin -s /bin/bash  # (if you have to use root permissions)

You may get a warning similar to this when entering these commands::

  warning: cannot change directory to /home/mediagoblin: No such file or directory

You can disregard this warning. To return to your regular user account after
using the system account, just enter ``exit``.

.. note::

    Unless otherwise noted, the remainder of this document assumes that all
    operations are performed using this unpriviledged account.

.. _create-mediagoblin-directory:

Create a MediaGoblin Directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You should create a working directory for MediaGoblin. This document
assumes your local git repository will be located at 
``/srv/mediagoblin.example.org/mediagoblin/``.
Substitute your prefered local deployment path as needed.

Setting up the working directory requires that we first create the directory
with elevated priviledges, and then assign ownership of the directory
to the unpriviledged system account.

To do this, enter either of the following commands, changing the defaults
to suit your particular requirements::

  sudo mkdir -p /srv/mediagoblin.example.org && sudo chown -hR mediagoblin:mediagoblin /srv/mediagoblin.example.org

or (as the root user)::

  mkdir -p /srv/mediagoblin.example.org && chown -hR mediagoblin:mediagoblin /srv/mediagoblin.example.org


Install MediaGoblin and Virtualenv
----------------------------------

.. note::

   MediaGoblin is still developing rapidly. As a result
   the following instructions recommend installing from the ``master``
   branch of the git repository. Eventually production deployments will
   want to transition to running from more consistent releases.

We will now clone the MediaGoblin source code repository and setup and
configure the necessary services. Modify these commands to
suit your own environment. As a reminder, you should enter these
commands using your unpriviledged system account.

Change to the MediaGoblin directory that you just created::

    cd /srv/mediagoblin.example.org

Clone the MediaGoblin repository and set up the git submodules::

    git clone git://gitorious.org/mediagoblin/mediagoblin.git
    cd mediagoblin
    git submodule init && git submodule update


And set up the in-package virtualenv::

    (virtualenv --system-site-packages . || virtualenv .) && ./bin/python setup.py develop

.. note::

   We presently have an **experimental** make-style deployment system.  if
   you'd like to try it, instead of the above command, you can run::

     ./experimental-bootstrap.sh && ./configure && make

   This also includes a number of nice features, such as keeping your
   viratualenv up to date by simply running `make update`.

   Note: this is liable to break.  Use this method with caution.

.. ::

   (NOTE: Is this still relevant?)

   If you have problems here, consider trying to install virtualenv
   with the ``--distribute`` or ``--no-site-packages`` options. If
   your system's default Python is in the 3.x series you may need to
   run ``virtualenv`` with the  ``--python=python2.7`` or
   ``--python=python2.6`` options.

The above provides an in-package install of ``virtualenv``. While this
is counter to the conventional ``virtualenv`` configuration, it is
more reliable and considerably easier to configure and illustrate. If
you're familiar with Python packaging you may consider deploying with
your preferred method.

Assuming you are going to deploy with FastCGI, you should also install
flup::

    ./bin/easy_install flup

(Sometimes this breaks because flup's site is flakey.  If it does for
you, try)::

    ./bin/easy_install https://pypi.python.org/pypi/flup/1.0.3.dev-20110405

This concludes the initial configuration of the development
environment. In the future, when you update your
codebase, you should also run::

    ./bin/python setup.py develop --upgrade && ./bin/gmg dbupdate && git submodule fetch

Note: If you are running an active site, depending on your server
configuration, you may need to stop it first or the dbupdate command
may hang (and it's certainly a good idea to restart it after the
update)


Deploy MediaGoblin Services
---------------------------

Edit site configuration
~~~~~~~~~~~~~~~~~~~~~~~

A few basic properties must be set before MediaGoblin will work. First
make a copy of ``mediagoblin.ini`` for editing so the original config
file isn't lost::

    cp mediagoblin.ini mediagoblin_local.ini

Then:
 - Set ``email_sender_address`` to the address you wish to be used as
   the sender for system-generated emails
 - Edit ``direct_remote_path``, ``base_dir``, and ``base_url`` if
   your mediagoblin directory is not the root directory of your
   vhost.


Configure MediaGoblin to use the PostgreSQL database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you are using postgres, edit the ``[mediagoblin]`` section in your
``mediagoblin_local.ini`` and put in::

    sql_engine = postgresql:///mediagoblin

if you are running the MediaGoblin application as the same 'user' as the
database owner.


Update database data structures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before you start using the database, you need to run::

    ./bin/gmg dbupdate

to populate the database with the MediaGoblin data structures.


Test the Server
~~~~~~~~~~~~~~~

At this point MediaGoblin should be properly installed.  You can
test the deployment with the following command::

    ./lazyserver.sh --server-name=broadcast

You should be able to connect to the machine on port 6543 in your
browser to confirm that the service is operable.

.. _webserver-config:


FastCGI and nginx
~~~~~~~~~~~~~~~~~

This configuration example will use nginx, however, you may
use any webserver of your choice as long as it supports the FastCGI
protocol. If you do not already have a web server, consider nginx, as
the configuration files may be more clear than the
alternatives.

Create a configuration file at
``/srv/mediagoblin.example.org/nginx.conf`` and create a symbolic link
into a directory that will be included in your ``nginx`` configuration
(e.g. "``/etc/nginx/sites-enabled`` or ``/etc/nginx/conf.d``) with
one of the following commands (as the root user)::

    ln -s /srv/mediagoblin.example.org/nginx.conf /etc/nginx/conf.d/
    ln -s /srv/mediagoblin.example.org/nginx.conf /etc/nginx/sites-enabled/

Modify these commands and locations depending on your preferences and
the existing configuration of your nginx instance. The contents of
this ``nginx.conf`` file should be modeled on the following::

    server {
     #################################################
     # Stock useful config options, but ignore them :)
     #################################################
     include /etc/nginx/mime.types;

     autoindex off;
     default_type  application/octet-stream;
     sendfile on;

     # Gzip
     gzip on;
     gzip_min_length 1024;
     gzip_buffers 4 32k;
     gzip_types text/plain text/html application/x-javascript text/javascript text/xml text/css;

     #####################################
     # Mounting MediaGoblin stuff
     # This is the section you should read
     #####################################

     # Change this to update the upload size limit for your users
     client_max_body_size 8m;

     # prevent attacks (someone uploading a .txt file that the browser
     # interprets as an HTML file, etc.)
     add_header X-Content-Type-Options nosniff;

     server_name mediagoblin.example.org www.mediagoblin.example.org;
     access_log /var/log/nginx/mediagoblin.example.access.log;
     error_log /var/log/nginx/mediagoblin.example.error.log;

     # MediaGoblin's stock static files: CSS, JS, etc.
     location /mgoblin_static/ {
        alias /srv/mediagoblin.example.org/mediagoblin/mediagoblin/static/;
     }

     # Instance specific media:
     location /mgoblin_media/ {
        alias /srv/mediagoblin.example.org/mediagoblin/user_dev/media/public/;
     }

     # Theme static files (usually symlinked in)
     location /theme_static/ {
        alias /srv/mediagoblin.example.org/mediagoblin/user_dev/theme_static/;
     }

     # Plugin static files (usually symlinked in)
     location /plugin_static/ {
        alias /srv/mediagoblin.example.org/mediagoblin/user_dev/plugin_static/;
     }

     # Mounting MediaGoblin itself via FastCGI.
     location / {
        fastcgi_pass 127.0.0.1:26543;
        include /etc/nginx/fastcgi_params;

        # our understanding vs nginx's handling of script_name vs
        # path_info don't match :)
        fastcgi_param PATH_INFO $fastcgi_script_name;
        fastcgi_param SCRIPT_NAME "";
     }
    }

Now, nginx instance is configured to serve the MediaGoblin
application. Perform a quick test to ensure that this configuration
works. Restart nginx so it picks up your changes, with a command that
resembles one of the following (as the root user)::

    sudo /etc/init.d/nginx restart
    sudo /etc/rc.d/nginx restart

Now start MediaGoblin. Use the following command sequence as an
example::

    cd /srv/mediagoblin.example.org/mediagoblin/
    ./lazyserver.sh --server-name=fcgi fcgi_host=127.0.0.1 fcgi_port=26543

Visit the site you've set up in your browser by visiting
<http://mediagoblin.example.org>. You should see MediaGoblin!

.. note::

   The configuration described above is sufficient for development and
   smaller deployments. However, for larger production deployments
   with larger processing requirements, see the
   ":doc:`production-deployments`" documentation.
   

Apache
~~~~~~

Instructions and scripts for running MediaGoblin on an Apache server
can be found on the `MediaGoblin wiki <http://wiki.mediagoblin.org/Deployment>`_.


Security Considerations
~~~~~~~~~~~~~~~~~~~~~~~

.. warning::

   The directory ``user_dev/crypto/`` contains some very
   sensitive files.
   Especially the ``itsdangeroussecret.bin`` is very important
   for session security. Make sure not to leak its contents anywhere.
   If the contents gets leaked nevertheless, delete your file
   and restart the server, so that it creates a new secret key.
   All previous sessions will be invalidated.

