=========
 Storage
=========


See for now: http://wiki.mediagoblin.org/Storage

Things get moved here.


The storage systems attached to your app
----------------------------------------

Dynamic content: queue_store and public_store
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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


StorageInterface and implementations
------------------------------------

The guts of StorageInterface and friends 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Writing code to store stuff
~~~~~~~~~~~~~~~~~~~~~~~~~~~
