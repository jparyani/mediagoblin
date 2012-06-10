======================
 flatpagesfile plugin
======================

This is the flatpages file plugin. It allows you to add pages to your
MediaGoblin instance which are not generated from user content. For
example, this is useful for these pages:

* About this site
* Terms of service
* Privacy policy
* How to get an account here
* ...


How to configure
================

Add the following to your MediaGoblin .ini file in the ``[plugins]``
section::

    [[mediagoblin.plugins.flatpagesfile]]


This tells MediaGoblin to load the flatpagesfile plugin. This is the
subsection that you'll do all flatpagesfile plugin configuration in.


How to add pages
================

To add a new page to your site, you need to do two things:

1. add a route to the MediaGoblin .ini file in the flatpagesfile
   subsection

2. write a template that will get served when that route is requested


Routes
------

First, let's talk about the route.

A route is a key/value in your configuration file.

The key starts with ``path`` and then has a number after that. For
example: ``path1``, ``path2``, ... ``path15``, ...

The value has three parts separated by commas:

1. **route name**: You can use this with `url()` in templates to have
   MediaGoblin automatically build the urls for you. It's very handy.

   It should be "unique" and it should be alphanumeric characters and
   hyphens. I wouldn't put spaces in there.

   Examples: ``flatpages-about``, ``about-view``, ``contact-view``, ...

2. **route path**: This is the url that this route matches.

   Examples: ``/about``, ``/contact``, ``/pages/about``, ...

   Technically, this is a regular expression and you can do anything
   with this that you can do with the routepath parameter of
   `routes.Route`. For more details, see `the routes documentation
   <http://routes.readthedocs.org/en/latest/>`_.

   Example: ``/siteadmin/{adminname:\w+}``

   .. Note::

      If you're doing something fancy, enclose the route in single
      quotes.

      For example: ``'/siteadmin/{adminname:\w+}'``

3. **template**: The template to use for this url. The template is in
   the flatpagesfile template directory, so you just need to specify
   the file name.

   Like with other templates, if it's an HTML file, it's good to use
   the ``.html`` extensions.

   Examples: ``index.html``, ``about.html``, ``contact.html``, ...


Here's an example configuration that adds two flat pages: one for an
"About this site" page and one for a "Terms of service" page::

    [[mediagoblin.plugins.flatpagesfile]]
    page1 = about-view, '/about', about.html
    page2 = terms-view, '/terms', terms.html


Templates
---------

To add pages, you must edit template files on the file system in your
`local_templates` directory.

The directory structure looks kind of like this::

    local_templates
    |- flatpagesfile
       |- flatpage1.html
       |- flatpage2.html
       |- ...


The ``.html`` file contains the content of your page. It's just a
template like all the other templates you have.

Here's an example that extends the `flatpagesfile/base.html`
template::

   {% extends "flatpagesfile/base.html" %}
   {% block mediagoblin_content %}
   <h1>About this site</h1>
   <p>
     This site is a MediaGoblin instance set up to host media for
     me, my family and my friends.
   </p>
   {% endblock %}


.. Note::

   If you have a bunch of flatpages that kind of look like one
   another, take advantage of Jinja2 template extending and create a
   base template that the others extend.

