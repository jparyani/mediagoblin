.. MediaGoblin Documentation

   Written in 2011, 2012 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

==========
Migrations
==========

So, about migrations.  Every time we change the way the database
structure works, we need to add a migration so that people running
older codebases can have their databases updated to the new structure
when they run `./bin/gmg dbupdate`.

The first time `./bin/gmg dbupdate` is run by a user, it creates the
tables at the current state that they're defined in models.py and sets
the migration number to the current migration... after all, migrations
only exist to get things to the current state of the db.  After that,
every migration is run with dbupdate.

There's a few things you need to know:

- We use `sqlalchemy-migrate
  <http://code.google.com/p/sqlalchemy-migrate/>`_.
  See `their docs <https://sqlalchemy-migrate.readthedocs.org/>`_.
- `Alembic <https://bitbucket.org/zzzeek/alembic>`_ might be a better
  choice than sqlalchemy-migrate now or in the future, but we
  originally decided not to use it because it didn't have sqlite
  support.  It's not clear if that's changed.
- SQLAlchemy has two parts to it, the ORM and the "core" interface.
  We DO NOT use the ORM when running migrations.  Think about it: the
  ORM is set up with an expectation that the models already reflect a
  certain pattern.  But if a person is moving from their old patern
  and are running tools to *get to* the current pattern, of course
  their current database structure doesn't match the state of the ORM!
- How to write migrations?  Maybe there will be a tutorial here in the
  future... in the meanwhile, look at existing migrations in
  `mediagoblin/db/migrations.py` and look in
  `mediagoblin/tests/test_sql_migrations.py` for examples.
- Common pattern: use `inspect_table` to get the current state
  of the table before we run alterations on it.
- Make sure you set the RegisterMigration to be the next migration in
  order.
- What happens if you're adding a *totally new* table?  In this case,
  you should copy the table in entirety as it exists into
  migrations.py then create the tables based off of that... see
  add_collection_tables.  This is easier than reproducing the SQL by
  hand.
- If you're writing a feature branch, you don't need to keep adding
  migrations every time you change things around if your database
  structure is in flux.  Just alter your migrations so that they're
  correct for the merge into master.

That's it for now!  Good luck!
