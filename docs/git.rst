==========================
 Git, Cloning and Patches
==========================

GNU MediaGoblin uses git for all our version control and we have
the repositories hosted on `Gitorious <http://gitorious.org/>`_.

We have two repositories.  One is for the project and the other is for
the project website.


How to clone the project
========================

Do::

    git clone git://gitorious.org/mediagoblin/mediagoblin.git


How to send in patches
======================

All patches should be tied to issues in the `issue tracker
<http://bugs.foocorp.net/projects/mediagoblin/issues>`_.
That makes it a lot easier for everyone to track proposed changes and
make sure your hard work doesn't get dropped on the floor!

If there isn't an issue for what you're working on, please create
one.  The better the description of what it is you're trying to
fix/implement, the better everyone else is able to understand why
you're doing what you're doing.

There are two ways you could send in a patch.


How to send in a patch from a publicly available clone
------------------------------------------------------

Add a comment to the issue you're working on with the following bits
of information:

* the url for your clone
* the revs you want looked at
* any details, questions, or other things that should be known


How to send in a patch if you don't have a publicly available clone
-------------------------------------------------------------------

Assuming that the remote is our repository on gitorious and the branch
to compare against is master, do the following:

1. checkout the branch you did your work in
2. do::

      git format-patch -o patches origin/master

3. either:

   * tar up and attach the tarball to the issue you're working on, OR
   * attach the patch files to the issue you're working on one at a
     time


How to learn git
================

Check out :ref:`hacking-howto-git`!
