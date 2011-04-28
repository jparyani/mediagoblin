.. _beardomatic-chapter:

===========================================
 Beardomatic: Infrastructure Documentation
===========================================

What the hell is Beardomatic?
=============================

You might be wondering, "Gah!  What the hell is Beardomatic!?"

Well, I'll tell you.  GNU MediaGoblin is a piece of software that sits
on a stack of libraries that do a bunch of stuff.  It makes it easier
to differentiate the bits of code that encompass GNU MediaGoblin from
the bits of code that GNU MediaGoblin sit on top of.  Thus, we came up
with the TOTALLY AWESOME name Beardomatic.

Now you might be saying, "Holy crap!?  Another web framework?  Are you
going to write a mocking framework and an enumeration library, too!?"

No, we're not.  We're just calling this Beardomatic so that it's
easier to talk about things.  However, at some point, we can take
these infrastructure bits from GNU MediaGoblin and turn them into a
full-blown "web framework".  We wouldn't do this to compete for
mindshare with other web frameworks.  We would do this to make it
easier for us to bootstrap other similar projects.


Beardomatic software stack
==========================

Beardomatic is a software stack "web framework" composed of the
following bits:

* Project infrastructure

  * `Python <http://python.org/>`_: the language we're using to write
    this

  * `Nose <http://somethingaboutorange.com/mrl/projects/nose/>`_:
    for unit tests

  * `buildout <http://www.buildout.org/>`_: for getting dependencies,
    building a runtime environment, ...

* Data storage

  * `MongoDB <http://www.mongodb.org/>`_: the document database backend
    for storage

* Web application

  * `Paste Deploy <http://pythonpaste.org/deploy/>`_ and 
    `Paste Script <http://pythonpaste.org/script/>`_: we'll use this for
    configuring and launching the application

  * `WebOb <http://pythonpaste.org/webob/>`_: nice abstraction layer
    from HTTP requests, responses and WSGI bits

  * `Routes <http://routes.groovie.org/>`_: for URL routing

  * `Beaker <http://beaker.groovie.org/>`_: for handling sessions

  * `Jinja2 <http://jinja.pocoo.org/docs/>`_: the templating engine

  * `MongoKit <http://namlook.github.com/mongokit/>`_: the lightweight
    ORM for MongoDB we're using which will make it easier to define
    structures and all that

  * `WTForms <http://wtforms.simplecodes.com/>`_: for handling,
    validation, and abstraction from HTML forms

  * `Celery <http://celeryproject.org/>`_: for task queuing (resizing
    images, encoding video, ...)

  * `RabbitMQ <http://www.rabbitmq.com/>`_: for sending tasks to celery

* Front end

  * `JQuery <http://jquery.com/>`_: for groovy JavaScript things


How to ... in Beardomatic?
==========================

FIXME - write this
