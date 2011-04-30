.. _codebase-chapter:

========================
 Codebase Documentation
========================

This chapter covers the libraries that GNU MediaGoblin uses as well as
various recipes for getting things done.


Software Stack
==============

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


Recipes
=======

FIXME - write this
