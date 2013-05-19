=========
 Storage
=========

The storage systems attached to your app
----------------------------------------

Dynamic content: queue_store and public_store
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Two instances of the StorageInterface come attached to your app. These 
are: 

+ **queue_store:** When a user submits a fresh piece of media for
  their gallery, before the Processing stage, that piece of media sits
  here in the queue_store. (It's possible that we'll rename this to
  "private_store" and start storing more non-publicly-stored stuff in
  the future...). This is a StorageInterface implementation
  instance. Visitors to your site probably cannot see it... it isn't
  designed to be seen, anyway.

+ **public_store:** After your media goes through processing it gets
  moved to the public store. This is also a StorageInterface
  implelementation, and is for stuff that's intended to be seen by
  site visitors.

The workbench
~~~~~~~~~~~~~

In addition, there's a "workbench" used during
processing...  it's just for temporary files during
processing, and also for making local copies of stuff that
might be on remote storage interfaces while transitionally
moving/converting from the queue_store to the public store. 
See the workbench module documentation for more.

.. automodule:: mediagoblin.tools.workbench
   :members:
   :show-inheritance:


Static assets / staticdirect
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On top of all that, there is some static media that comes bundled with your
application. This stuff is kept in: 

   mediagoblin/static/

These files are for mediagoblin base assets. Things like the CSS files, 
logos, etc. You can mount these at whatever location is appropriate to you
(see the direct_remote_path option in the config file) so if your users 
are keeping their static assets at http://static.mgoblin.example.org/ but 
their actual site is at http://mgoblin.example.org/, you need to be able 
to get your static files in a where-it's-mounted agnostic way. There's a 
"staticdirector" attached to the request object. It's pretty easy to use;
just look at this bit taken from the 
mediagoblin/templates/mediagoblin/base.html main template:

    <link rel="stylesheet" type="text/css" 
        href="Template:Request.staticdirect('/css/extlib/text.css')"/>

see? Not too hard. As expected, if you configured direct_remote_path to be 
http://static.mgoblin.example.org/ you'll get back 
http://static.mgoblin.example.org/css/extlib/text.css just as you'd 
probably expect. 

StorageInterface and implementations
------------------------------------

The guts of StorageInterface and friends 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

So, the StorageInterface!

So, the public and queue stores both use StorageInterface implementations
... but what does that mean? It's not too hard.

Open up: 

    mediagoblin/storage.py

In here you'll see a couple of things. First of all, there's the 
StorageInterface class. What you'll see is that this is just a very simple
python class. A few of the methods actually implement things, but for the
most part, they don't. What really matters about this class is the 
docstrings. Each expected method is documented as to how it should be 
constructed. Want to make a new StorageInterface? Simply subclass it. Want 
to know how to use the methods of your storage system? Read these docs, 
they span all implementations.

There are a couple of implementations of these classes bundled in 
storage.py as well. The most simple of these is BasicFileStorage, which is 
also the default storage system used. As expected, this stores files 
locally on your machine.

There's also a CloudFileStorage system. This provides a mapping to 
[OpenStack's swift http://swift.openstack.org/] storage system (used by 
RackSpace Cloud files and etc).

Between these two examples you should be able to get a pretty good idea of
how to write your own storage systems, for storing data across your 
beowulf cluster of radioactive monkey brains, whatever. 

Writing code to store stuff
~~~~~~~~~~~~~~~~~~~~~~~~~~~

So what does coding for StorageInterface implementations actually look 
like? It's pretty simple, really. For one thing, the design is fairly 
inspired by [Django's file storage API 
https://docs.djangoproject.com/en/dev/ref/files/storage/]... with some 
differences.

Basically, you access files on "file paths", which aren't exactly like 
unix file paths, but are close. If you wanted to store a file on a path 
like dir1/dir2/filename.jpg you'd actually write that file path like:

['dir1', 'dir2', 'filename.jpg']

This way we can be *sure* that each component is actually a component of
the path that's expected... we do some filename cleaning on each component.

Your StorageInterface should pass in and out "file like objects". In other 
words, they should provide .read() and .write() at minimum, and probably 
also .seek() and .close(). 
