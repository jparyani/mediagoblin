=======
 Stack
=======

The software stack for this project might change over time, but this
is what we're thinking right now.

There's some explanation of design decisions in the
:ref:`design-decisions-chapter`.


Python
======

* http://python.org/

The core team does a lot of work in Python and it's the language we're
most likely to do a project like this in.


MongoDB
=======

* http://www.mongodb.org/

A "document database".  Because it's extremely flexible and scales up
well, but I guess not down well.


MongoKit
========

* http://namlook.github.com/mongokit/

A lightweight ORM for mongodb.  Helps us define our structures better,
does schema validation, schema evolution, and helps make things more
fun and pythonic.


Jinja2
======

* http://jinja.pocoo.org/docs/

For templating.  Pretty much django templates++ but allows us to pass
arguments into method calls instead of writing custom tags.


WTForms
=======

* http://wtforms.simplecodes.com/

For form handling, validation, abstraction.  Almost just like Django's
templates.


WebOb
=====

* http://pythonpaste.org/webob/

Gives nice request/response objects (also somewhat Django-ish).


Paste Deploy and Paste Script
=============================

* http://pythonpaste.org/deploy/
* http://pythonpaste.org/script/

This will be the default way of configuring and launching the
application.  Since GNU MediaGoblin will be fairly WSGI minimalist though,
you can probably use other ways to launch it, though this will be the
default.


Routes
======

* http://routes.groovie.org/

For URL Routing.  It works well enough.


JQuery
======

* http://jquery.com/

For all sorts of things on the JavaScript end of things, for all sorts
of reasons.


Beaker
======

* http://beaker.groovie.org/

For sessions, because that seems like it's generally considered the
way to go I guess.


Nose
====

* http://somethingaboutorange.com/mrl/projects/nose/1.0.0/

For unit tests because it makes testing a bit nicer.


Celery
======

* http://celeryproject.org/

For task queueing (resizing images, encoding video, ...).


RabbitMQ
========

* http://www.rabbitmq.com/

For sending tasks to celery, because I guess that's what most people
do.  Might be optional, might also let people use MongoDB for this if
they want.
