.. _original-design-decisions-chapter:

===========================
 Original Design Decisions
===========================

.. contents:: Sections
   :local:


This chapter talks a bit about design decisions.

Note: This is an outdated document.  It's more or less the historical
reasons for a lot of things.  That doesn't mean these decisions have
stayed the same or we haven't changed our minds on some things!


Why GNU MediaGoblin?
====================

Chris and Will on "Why GNU MediaGoblin":

    Chris came up with the name MediaGoblin.  The name is pretty fun.
    It merges the idea that this is a Media hosting project with
    Goblin which sort of sounds like gobbling.  Here's a piece of
    software that gobbles up your media for all to see.

    `According to Wikipedia <http://en.wikipedia.org/wiki/Goblin>`_, a
    goblin is:

        a legendary evil or mischievous illiterate creature, described
        as grotesquely evil or evil-like phantom

    So are we evil?  No.  Are we mischievous or illiterate?  Not
    really.  So what kind of goblin are we thinking about?  We're
    thinking about these goblins:

    .. figure:: ../_static/goblin.png
       :alt: Cute goblin with a beret.

       *Figure 1: Cute goblin with a beret.  llustrated by Chris
       Webber*

    .. figure:: ../_static/snugglygoblin.png
       :scale: 50%
       :alt: Snuggly goblin with a beret.

       *Figure 2: Snuggly goblin.  Illustrated by Karen Rustad*

    Those are pretty cute goblins.  Those are the kinds of goblins
    we're thinking about.

    Chris started doing work on the project after thinking about it
    for a year.  Then, after talking with Matt and Rob, it became an
    official GNU project.  Thus we now call it GNU MediaGoblin.

    That's a lot of letters, though, so in the interest of brevity and
    facilitating easier casual conversation and balancing that with
    what's important to us, we have the following rules:

    1. "GNU MediaGoblin" is the name we're going to use in all official
       capacities: web site, documentation, press releases, ...

    2. In casual conversation, it's ok to use more casual names.

    3. If you're writing about the project, we ask that you call it GNU 
       MediaGoblin.

    4. If you don't like the name, we kindly ask you to take a deep
       breath, think a happy thought about cute little goblins playing
       on a playground and taking cute pictures of themselves, and let
       it go.  (Will added this one.)


Why Python
==========

Chris Webber on "Why Python":

    Because I know Python, love Python, am capable of actually making
    this thing happen in Python (I've worked on a lot of large free
    software web applications before in Python, including `Miro
    Community`_, the `Miro Guide`_, a large portion of `Creative
    Commons`_, and a whole bunch of things while working at `Imaginary
    Landscape`_).  Me starting a project like this makes sense if it's
    done in Python.

    You might say that PHP is way more deployable, that Rails has way
    more cool developers riding around on fixie bikes---and all of
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

    If you notice in the technology list I list a lot of components
    that are very "django-like", but not actually `Django`_
    components.  What can I say, I really like a lot of the ideas in
    Django!  Which leads to the question: why not just use Django?

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

.. _Django: http://www.djangoproject.com/
.. _Pylons: http://pylonshq.com/
.. _Pyramid: http://docs.pylonsproject.org/projects/pyramid/dev/
.. _Flask: http://flask.pocoo.org/

.. [1] http://pythonpaste.org/webob/do-it-yourself.html
.. [2] http://pycon.blip.tv/file/4881071/


Why MongoDB
===========

(Note: We don't use MongoDB anymore.  This is the original rationale,
however.)

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

    `Sphinx`_ is a fantastic tool for organizing documentation for a
    Python-based project that makes it pretty easy to write docs that
    are readable in source form and can be "compiled" into HTML, LaTeX
    and other formats.

    There are other doc systems out there, but given that GNU
    MediaGoblin is being written in Python and I've done a ton of
    documentation using Sphinx, it makes sense to use Sphinx for now.

.. _Sphinx: http://sphinx.pocoo.org/


Why AGPLv3 and CC0?
===================

Chris, Brett, Will, Rob, Matt, et al curated into a story where
everyone is the hero by Will on "Why AGPLv3 and CC0":

    The `AGPL v3`_ preserves the freedoms guaranteed by the GPL v3 in
    the context of software as a service.  Using this license ensures
    that users of the service have the ability to examine the source,
    deploy their own instance, and implement their own version.  This
    is really important to us and a core mission component of this
    project.  Thus we decided that the software parts should be under
    this license.

    However, the project is made up of more than just software:
    there's CSS, images, and other output-related things.  We wanted
    the templates/images/css side of the project all permissive and
    permissive in the same absolutely permissive way.  We're waiving
    our copyrights to non-software things under the CC0 waiver.

    That brings us to the templates where there's some code and some
    output.  The template engine we're using is called Jinja2.  It
    mixes HTML markup with Python code to render the output of the
    software.  We decided the templates are part of the output of the
    software and not the software itself.  We wanted the output of the
    software to be licensed in a hassle-free way so that when someone
    deploys their own GNU MediaGoblin instance with their own
    templates, they don't have to deal with the copyleft aspects of
    the AGPLv3 and we'd be fine with that because the changes they're
    making are identity-related.  So at first we decided to waive our
    copyrights to the templates with a CC0 waiver and then add an
    exception to the AGPLv3 for the software such that the templates
    can make calls into the software and yet be a separately licensed
    work.  However, Brett brought up the question of whether this
    allows some unscrupulous person to make changes to the software
    through the templates in such a way that they're not bound by the
    AGPLv3: i.e. a loophole.  We thought about this loophole and
    between this and the extra legalese involved in the exception to
    the AGPLv3, we decided that it's just way simpler if the templates
    were also licensed under the AGPLv3.

    Then we have the licensing for the documentation.  Given that the
    documentation is tied to the software content-wise, we don't feel
    like we have to worry about ensuring freedom of the documentation
    or worry about attribution concerns.  Thus we're waiving our
    copyrights to the documentation under CC0 as well.

    Lastly, we have branding.  This covers logos and other things that
    are distinctive to GNU MediaGoblin that we feel represents this
    project.  Since we don't currently have any branding, this is an
    open issue, but we're thinking we'll go with a CC BY-SA license.

    By licensing in this way, we make sure that users of the software
    receive the freedoms that the AGPLv3 ensures regardless of what
    fate befalls this project.

    So to summarize:

    * software (Python, JavaScript, HTML templates): licensed
      under AGPLv3
    * non-software things (CSS, images, video): copyrights waived
      under CC0 because this is output of the software
    * documentation: copyrights waived under CC0 because it's not part
      of the software
    * branding assets: we're kicking this can down the road, but
      probably CC BY-SA

    This is all codified in the ``COPYING`` file.

.. _AGPL v3: http://www.gnu.org/licenses/agpl.html
.. _CC0 v1: http://creativecommons.org/publicdomain/zero/1.0/


Why (non-mandatory) copyright assignment?
=========================================

Chris Webber on "Why copyright assignment?":

    GNU MediaGoblin is a GNU project with non-mandatory but heavily
    encouraged copyright assignment to the FSF.  Most, if not all, of
    the core contributors to GNU MediaGoblin will have done a
    copyright assignment, but unlike some other GNU projects, it isn't
    required here.  We think this is the best choice for GNU
    MediaGoblin: it ensures that the Free Software Foundation may
    protect the software by enforcing the AGPL if the FSF sees fit,
    but it also means that we can immediately merge in changes from a
    new contributor.  It also means that some significant non-FSF
    contributors might also be able to enforce the AGPL if seen fit.

    Again, assignment is not mandatory, but it is heavily encouraged,
    even incentivized: significant contributors who do a copyright
    assignment to the FSF are eligible to have a unique goblin drawing
    produced for them by the project's main founder, Christopher Allan
    Webber.  See `the wiki <http://wiki.mediagoblin.org/>`_ for details.


