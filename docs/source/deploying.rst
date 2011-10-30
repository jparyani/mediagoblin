.. _deployment-chapter:

=======================
 Deploying MediaGoblin
=======================

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

Install dependencies
====================

First thing you want to do is install necessary dependencies.  Those
are, roughly:

 - Python 2.6 or 2.7
 - python-lxml - http://lxml.de/
 - git - http://git-scm.com/
 - MongoDB - http://www.mongodb.org/
 - Python Imaging Library (PIL) - http://www.pythonware.com/products/pil/
 - virtualenv - http://www.virtualenv.org/ 

On a .deb based system (Debian, GnewSense, Trisquel, Ubuntu, etc) run
the following:

  sudo apt-get install mongodb git-core python python-dev \
    python-lxml python-imaging python-virtualenv 

On a .rpm based system (Fedora, RedHat, etc):

  yum install mongodb-server python-paste-deploy python-paste-script \
    git-core python python-devel python-lxml python-imaging python-virtualenv

Configure MongoDB
=================

So you have MongoDB installed... you should probably make sure that
you have a few things configured before you start up MediaGoblin.

For one thing, you almost certainly want to make sure `journaling
<http://www.mongodb.org/display/DOCS/Journaling>`_ is enabled.
Journaling is automatically enabled on 64 bit systems post-MongoDB
2.0, but you should check.  (Not turning on journaling means that if
your server crashes you have a good chance of losing data!)

MongoDB can take a lot of space by default.  If you're planning on
running a smaller instance, consider following our `scaling down
<http://wiki.mediagoblin.org/Scaling_Down>`_ guide (keeping in mind
that the steps recommended here are tradeoffs!).


Decide on a non-privileged user
===============================

As MediaGoblin does not require any special permissions, you
should either decide on a user to run it as, or even better create a
dedicated user for it. Consult your distribution's documentation on
how to create dedicated service user. Make sure it does have a locked
password, so nobody can login using this user.

You should create a working dir for MediaGoblin. We assume you will
check things out into /srv/mediagoblin.example.org/mediagoblin/ for
this documentation, but you can choose whatever fits your local needs.

Most of the remaining documentation assumes you're working as that
user. As root, you might want to do "su - mediagoblinuser".


Install MediaGoblin and Virtualenv
==================================

For the moment, let's assume you want to run the absolute most
bleeding edge version of mediagoblin in mediagoblin master (possibly
not the best choice in a production environment, so these docs should
be fixed ;)).

Change to (and possibly make) the appropriate parent directory:

  cd /srv/mediagoblin.example.org/

Clone the repository:

  git clone git://gitorious.org/mediagoblin/mediagoblin.git

And setup the in-package virtualenv:

  cd mediagoblin
  virtualenv . && ./bin/python setup.py develop

(If you have problems here, consider trying to install virtualenv with
one of the flags --distribute or --no-site-packages... Additionally if
your system has python3.X as the default you might need to do
virtualenv --python=python2.7 or --python=python2.6)

(You might note that we've done an in-package install of
virtualenv... this isn't the most traditional way to install
virtualenv, and it might not even be the best.  But it's the easiest
to explain without having to explain python packaging, and it works.)

At this point your development environment should be setup.  You don't
need to do anything else.  However if at any point you update your
codebase, you should also run:

  ./bin/python setup.py develop --upgrade && ./bin/gmg migrate. 


Test-start the server
=====================

At this point mediagoblin should be properly installed.  You can
test-start it like so:

  ./lazyserver.sh --server-name=broadcast

You should be able to connect to the machine on port 6543 in your
browser to ensure that things are working.


Hook up to your webserver via fastcgi
=====================================

This section describes how to configure MediaGoblin to work via
fastcgi.  Our configuration example will use nginx, as the author of
this manual feels that nginx config files are easier to understand if
you have no experience with any type of configuration file.  However,
the translations to apache are not too hard.

Also for the sake of this document, we'll assume you're running
mediagoblin on the domain mediagoblin.example.org and your
mediagoblin checkout in /srv/mediagoblin.example.org/mediagoblin/

Now in reality, you won't be running mediagoblin on such a domain or
in such a directory, but it should be easy enough to move your stuff
over.

Anyway, in such an environment, make a config file in the normal place
you'd make such an nginx config file... probably
/etc/nginx/sites-available/mediagoblin.example.conf (and symlink said
file over to /etc/nginx/sites-enabled/ to turn it on)

Now put in that file:

  server {
    #################################################
    # Stock useful config options, but ignore them :)
    #################################################
    server_name mediagoblin.example.org www.mediagoblin.example.org;
    include /etc/nginx/mime.types;
  
    access_log /var/log/nginx/mediagoblin.example.access.log;
    error_log /var/log/nginx/mediagoblin.example.error.log;
  
    autoindex off;
    default_type  application/octet-stream;
    sendfile on;
    # tcp_nopush on;
  
    # Gzip
    gzip on;
    gzip_min_length 1024;
    gzip_buffers 4 32k;
    gzip_types text/plain text/html application/x-javascript text/javascript text/xml text/css;
  
    #####################################
    # Mounting MediaGoblin stuff
    # This is the section you should read
    #####################################
  
    # MediaGoblin's stock static files: CSS, JS, etc.
    location /mgoblin_static/ {
      alias /srv/mediagoblin.example.org/mediagoblin/static/;
    }
  
    # Instance specific media:
    location /mgoblin_media/ {
      alias /srv/mediagoblin.example.org/mediagoblin/user_dev/media/public/;
    }
  
    # Mounting MediaGoblin itself via fastcgi.
    location / {
      fastcgi_pass 127.0.0.1:26543;
      include /etc/nginx/fastcgi_params;
    }
  }

At this point your config file should be properly set up to handle
serving mediagoblin.  Now all you need to do is run it!

Let's do a quick test.  Restart nginx so it picks up your changes,
something probably like:

  sudo /etc/init.d/nginx restart

Now start up MediaGoblin.  "cd" to the MediaGoblin checkout and run:

  ./lazyserver.sh --server-name=fcgi fcgi_host=127.0.0.1 fcgi_port=26543

Visit the site you've set up in your browser, eg
http://example.mediagoblin.org (except with the real domain name or IP
you're expecting to use. ;))

