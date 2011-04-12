.. _design-decisions-chapter:

==================
 Design Decisions
==================

This chapter talks a bit about design decisions.


Why Python
==========

Chris Webber on "Why Python":

    Because I know Python, love Python, am capable of actually making
    this thing happen in Python (I've worked on a lot of large free
    software web applications before in Python, including `Miro
    Community`_, the `Miro Guide`_, a large portion of `Creative
    Commons`_, and a whole bunch of things while working at `Imaginary
    Landscape`_).  I know Python, I can make this happen in Python, me
    starting a project like this makes sense if it's done in Python.

    You might say that PHP is way more deployable, that Rails has way
    more cool developers riding around on fixie bikes, and all of
    those things are true.  But I know Python, like Python, and think
    that Python is pretty great.  I do think that deployment in Python
    is not as good as with PHP, but I think the days of shared hosting
    are (thankfully) coming to an end, and will probably be replaced
    by cheap virtual machines spun up on the fly for people who want
    that sort of stuff, and Python will be a huge part of that future,
    maybe even more than PHP will.  The deployment tools are getting
    better.  Maybe we can use something like Silver Lining.  Maybe we
    can just distribute as ``.debs`` or ``.rpms``.  We'll figure it
    out when we get there.

    Regardless, if I'm starting this project, which I am, it's gonna
    be in Python.

.. _Miro Community: http://mirocommunity.org/
.. _Miro Guide: http://miroguide.org/
.. _Creative Commons: http://creativecommons.org/
.. _Imaginary Landscape: http://www.imagescape.com/


Why WSGI Minimalism
===================

Chris Webber on "Why WSGI Minimalism":

    If you notice in the technology listI list a lot of
    components that are very `Django Project`_, but not actually
    Django components.  What can I say, I really like a lot of the
    ideas in Django!  Which leads to the question: why not just use
    Django?

    While I really like Django's ideas and a lot of its components, I
    also feel that most of the best ideas in Django I want have been
    implemented as good or even better outside of Django.  I could
    just use Django and replace the templating system with Jinja2, and
    the form system with wtforms, and the database with MongoDB and
    MongoKit, but at that point, how much of Django is really left?

    I also am sometimes saddened and irritated by how coupled all of
    Django's components are.  Loosely coupled yes, but still coupled.
    WSGI has done a good job of providing a base layer for running
    applications on and if you know how to do it yourself [1]_, it's
    not hard or many lines of code at all to bind them together
    without any framework at all (not even say `Pylons`_, `Pyramid`_
    or `Flask`_ which I think are still great projects, especially for
    people who want this sort of thing but have no idea how to get
    started).  And even at this already really early stage of writing
    MediaGoblin, that glue work is mostly done.

    Not to say I don't think Django isn't great for a lot of things.
    For a lot of stuff, it's still the best, but not for MediaGoblin,
    I think.

    One thing that Django does super well though is documentation.  It
    still has some faults, but even with those considered I can hardly
    think of any other project in Python that has as nice of
    documentation as Django.  It may be worth learning some lessons on
    documentation from Django [2]_, on that note.

    I'd really like to have a good, thorough hacking-howto and
    deployment-howto, especially in the former making some notes on
    how to make it easier for Django hackers to get started.

.. _Django Project: http://www.djangoproject.com/
.. _Pylons: http://pylonshq.com/
.. _Pyramid: http://docs.pylonsproject.org/projects/pyramid/dev/
.. _Flask: http://flask.pocoo.org/

.. [1] http://pythonpaste.org/webob/do-it-yourself.html
.. [2] http://pycon.blip.tv/file/4881071/


Why MongoDB
===========

Chris Webber on "Why MongoDB":

    In case you were wondering, I am not a NOSQL fanboy, I do not go
    around telling people that MongoDB is web scale.  Actually my
    choice for MongoDB isn't scalability, though scaling up really
    nicely is a pretty good feature and sets us up well in case large
    volume sites eventually do use MediaGoblin.  But there's another
    side of scalability, and that's scaling down, which is important
    for federation, maybe even more important than scaling up in an
    ideal universe where everyone ran servers out of their own
    housing.  As a memory-mapped database, MongoDB is pretty hungry,
    so actually I spent a lot of time debating whether the inability
    to scale down as nicely as something like SQL has with sqlite
    meant that it was out.

    But I decided in the end that I really want MongoDB, not for
    scalability, but for flexibility.  Schema evolution pains in SQL
    are almost enough reason for me to want MongoDB, but not quite.
    The real reason is because I want the ability to eventually handle
    multiple media types through MediaGoblin, and also allow for
    plugins, without the rigidity of tables making that difficult.  In
    other words, something like::

        {"title": "Me talking until you are bored",
         "description": "blah blah blah",
         "media_type": "audio",
         "media_data": {
             "length": "2:30",
             "codec": "OGG Vorbis"},
         "plugin_data": {
             "licensing": {
                 "license": "http://creativecommons.org/licenses/by-sa/3.0/"}}}


    Being able to just dump media-specific information in a media_data
    hashtable is pretty great, and even better is having a plugin
    system where you can just let plugins have their own entire
    key-value space cleanly inside the document that doesn't interfere
    with anyone else's stuff.  If we were to let plugins to deposit
    their own information inside the database, either we'd let plugins
    create their own tables which makes SQL migrations even harder
    than they already are, or we'd probably end up creating a table
    with a column for key, a column for value, and a column for type
    in one huge table called "plugin_data" or something similar.  (Yo
    dawg, I heard you liked plugins, so I put a database in your
    database so you can query while you query.)  Gross.

    I also don't want things to be too loose so that we forget or lose
    the structure of things, and that's one reason why I want to use
    MongoKit, because we can cleanly define a much structure as we
    want and verify that documents match that structure generally
    without adding too much bloat or overhead (MongoKit is a pretty
    lightweight wrapper and doesn't inject extra MongoKit-specific
    stuff into the database, which is nice and nicer than many other
    ORMs in that way).


Why Sphinx for documentation
============================

Will Kahn-Greene on "Why Sphinx":

    Sphinx is a fantastic tool for organizing documentation for a
    Python-based project that makes it pretty easy to write docs that
    are readable in source form and can be "compiled" into HTML, LaTeX
    and other formats.

    There are other doc systems out there, but given that GNU
    MediaGoblin is being written in Python, it makes sense to use
    Sphinx for now.
