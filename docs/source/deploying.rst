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

Install MediaGoblin and Virtualenv
==================================

For the moment, let's assume you want to run the absolute most
bleeding edge version of mediagoblin in mediagoblin master (possibly
not the best choice in a production environment, so these docs should
be fixed ;)).

Clone the repository:

  git clone git://gitorious.org/mediagoblin/mediagoblin.git

And setup the in-package virtualenv:

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


