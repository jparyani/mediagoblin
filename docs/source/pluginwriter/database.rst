.. MediaGoblin Documentation

   Written in 2013 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.


========
Database
========


Accessing Existing Data
=======================

If your plugin wants to access existing data, this is quite
straight forward. Just import the appropiate models and use
the full power of SQLAlchemy. Take a look at the (upcoming)
database section in the Developer's Chapter.


Creating new Tables
===================

If your plugin needs some new space to store data, you
should create a new table.  Please do not modify core
tables.  Not doing so might seem inefficient and possibly
is.  It will help keep things sane and easier to upgrade
versions later.

So if you create a new plugin and need new tables, create a
file named ``models.py`` in your plugin directory. You
might take a look at the core's db.models for some ideas.
Here's a simple one:

.. code-block:: python

    from mediagoblin.db.base import Base
    from sqlalchemy import Column, Integer, Unicode, ForeignKey

    class MediaSecurity(Base):
        __tablename__ = "yourplugin__media_security"

        # The primary key *and* reference to the main media_entry
        media_entry = Column(Integer, ForeignKey('core__media_entries.id'),
            primary_key=True)
        get_media_entry = relationship("MediaEntry",
            backref=backref("security_rating", cascade="all, delete-orphan"))

        rating = Column(Unicode)

    MODELS = [MediaSecurity]

That's it.

Some notes:

* Make sure all your ``__tablename__`` start with your
  plugin's name so the tables of various plugins can't
  conflict in the database. (Conflicts in python naming are
  much easier to fix later).
* Try to get your database design as good as possible in
  the first attempt.  Changing the database design later,
  when people already have data using the old design, is
  possible (see next chapter), but it's not easy.


Changing the Database Schema Later
==================================

If your plugin is in use and instances use it to store some
data, changing the database design is a tricky thing.

1. Make up your mind how the new schema should look like.
2. Change ``models.py`` to contain the new schema. Keep a
   copy of the old version around for your personal
   reference later.
3. Now make up your mind (possibly using your old and new
   ``models.py``) what steps in SQL are needed to convert
   the old schema to the new one.
   This is called a "migration".
4. Create a file ``migrations.py`` that will contain all
   your migrations and add your new migration.

Take a look at the core's ``db/migrations.py`` for some
good examples on what you might be able to do. Here's a
simple one to add one column:

.. code-block:: python

    from mediagoblin.db.migration_tools import RegisterMigration, inspect_table
    from sqlalchemy import MetaData, Column, Integer

    MIGRATIONS = {}

    @RegisterMigration(1, MIGRATIONS)
    def add_license_preference(db):
        metadata = MetaData(bind=db.bind)

        security_table = inspect_table(metadata, 'yourplugin__media_security')

        col = Column('security_level', Integer)
        col.create(security_table)
        db.commit()
