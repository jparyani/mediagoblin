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

Note: these tools are for administrators wanting to deploy a fresh
install.  If instead you want to join in as a contributor, see our
`Hacking HOWTO <http://wiki.mediagoblin.org/HackingHowto>`_ instead.

Prepare System
--------------

Dependencies
~~~~~~~~~~~~

MediaGoblin has the following core dependencies:

- Python 2.6 or 2.7
- `python-lxml <http://lxml.de/>`_
- `git <http://git-scm.com/>`_
- `MongoDB <http://www.mongodb.org/>`_
- `Python Imaging Library <http://www.pythonware.com/products/pil/>`_  (PIL)
- `virtualenv <http://www.virtualenv.org/>`_

On a DEB-based system (e.g Debian, gNewSense, Trisquel, Ubuntu, and
derivatives) issue the following command: ::

  sudo apt-get install mongodb git-core python python-dev python-lxml python-imaging python-virtualenv

On a RPM-based system (e.g. Fedora, RedHat, and derivatives) issue the
following command: ::

  yum install mongodb-server python-paste-deploy python-paste-script git-core python python-devel python-lxml python-imaging python-virtualenv

Configure MongoDB
~~~~~~~~~~~~~~~~~

After installing MongoDB some preliminary database configuration may
be necessary.

Ensure that MongoDB `journaling <http://www.mongodb.org/display/DOCS/Journaling>`_
is enabled. Journaling is enabled by default in version 2.0 and later
64-bit MongoDB instances. Check your deployment, and consider enabling
journaling if you're running 32-bit systems or earlier version.

.. warning::

   Running MongoDB without journaling risks general data corruption
   and raises the possibility of losing data within a 60-second
   window when the server restarts.

   MediaGoblin recommends enabling MongoDB's journaling feature by
   adding a ``--journal`` flag to the command line or a "``journal:
   true``" option to the configuration file.

MongoDB can take a lot of space by default. If you're planning on
running a smaller instance, consider the `scaling down guide
<http://wiki.mediagoblin.org/Scaling_Down>`_ for some appropriate
tradeoffs to conserve space.

Drop Privileges for MediaGoblin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As MediaGoblin does not require special permissions or elevated
access, you should run MediaGoblin under an existing non-root user or
preferably create a dedicated user for the purpose of running
MediaGoblin. Consult your distribution's documentation on how to
create "system account" or dedicated service user. Ensure that it is
not possible to log in to your system with as this user.

You should create a working directory for MediaGoblin. This document
assumes your local git repository will be located at  ``/srv/mediagoblin.example.org/mediagoblin/``
for this documentation. Substitute your prefer ed local deployment path
as needed.

This document assumes that all operations are performed as this
user. To drop privileges to this user, run the following command: ::


      su - [mediagoblin]``

Where, "``[mediagoblin]`` is the username of the system user that will
run MediaGoblin.

Install MediaGoblin and Virtualenv
----------------------------------

As of |version|, MediaGoblin has a rapid development pace. As a result
the following instructions recommend installing from the ``master``
branch of the git repository. Eventually production deployments will
want to transition to running from more consistent releases.

Issue the following commands, to create and change the working
directory. Modify these commands to reflect your own environment: ::

     mkdir -p /srv/mediagoblin.example.org/
     cd /srv/mediagoblin.example.org/

Clone the MediaGoblin repository: ::

     git clone git://gitorious.org/mediagoblin/mediagoblin.git

And setup the in-package virtualenv: ::

     cd mediagoblin
     virtualenv . && ./bin/python setup.py develop

.. note::

   If you have problems here, consider trying to install virtualenv
   with the ``--distribute`` or ``--no-site-packages`` options. If
   your system's default Python is in the 3.x series you man need to
   run ``virtualenv`` with the  ``--python=python2.7`` or
   ``--python=python2.6`` options.

The above provides an in-package install of ``virtualenv``. While this
is counter to the conventional ``virtualenv`` configuration, it is
more reliable and considerably easier to configure and illustrate. If
you're familiar with Python packaging you may consider deploying with
your preferred the method.

Assuming you are going to deploy with fastcgi, you should also install
flup: ::

     ./bin/easy_install flup

This concludes the initial configuration of the development
environment. In the future, if at any point you want update your
codebase, you should also run: ::

     ./bin/python setup.py develop --upgrade && ./bin/gmg migrate.

Deploy MediaGoblin Services
---------------------------

Test the Server
~~~~~~~~~~~~~~~

At this point MediaGoblin should be properly installed.  You can
test the deployment with the following command: ::

     ./lazyserver.sh --server-name=broadcast

You should be able to connect to the machine on port 6543 in your
browser to confirm that the service is operable.

Connect the Webserver to MediaGoblin with FastCGI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section describes how to configure MediaGoblin to work via
fastcgi. Our configuration example will use nginx, however, you may
use any webserver of your choice as long as it supports the FastCGI
protocol. If you do not already have a web server, consider nginx, as
the configuration files may be more clear than the
alternatives.

Create a configuration file at
``/srv/mediagoblin.example.org/nginx.conf`` and create a symbolic link
into a directory that will be included in your ``nginx`` configuration
(e.g. "``/etc/nginx/sites-enabled`` or ``/etc/nginx/conf.d``) with
one of the following commands (as the root user:) ::

     ln -s /srv/mediagoblin.example.org/nginx.conf /etc/nginx/conf.d/
     ln -s /srv/mediagoblin.example.org/nginx.conf /etc/nginx/sites-enabled/

Modify these commands and locations depending on your preferences and
the existing configuration of your nginx instance. The contents of
this ``nginx.conf`` file should be modeled on the following: ::

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

      # Mounting MediaGoblin itself via fastcgi.
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
resembles one of the following (as the root user:) ::

     sudo /etc/init.d/nginx restart
     sudo /etc/rc.d/nginx restart

Now start MediaGoblin. Use the following command sequence as an
example: ::

     cd /srv/mediagoblin.example.org/mediagoblin/
     ./lazyserver.sh --server-name=fcgi fcgi_host=127.0.0.1 fcgi_port=26543

Visit the site you've set up in your browser by visiting
<http://mediagobilin.example.org>. You should see MediaGoblin!

.. note::

   The configuration described above is sufficient for development and
   smaller deployments. However, for larger production deployments
   with larger processing requirements, see the
   ":doc:`production-deployments`" documentation.
