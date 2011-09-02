# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 MediaGoblin contributors.  See AUTHORS.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Database Abstraction/Wrapper Layer
==================================

  **NOTE from Chris Webber:** I asked Elrond to explain why he put
  ASCENDING and DESCENDING in db/util.py when we could just import from
  pymongo.  Read beow for why, but note that nobody is actually doing
  this and there's no proof that we'll ever support more than
  MongoDB... it would be a huge amount of work to do so.
  
  If you really want to prove that possible, jump on IRC and talk to
  us about making such a branch.  In the meanwhile, it doesn't hurt to
  have things as they are... if it ever makes it hard for us to
  actually do things, we might revisit or remove this.  But for more
  information, read below.

This submodule is for most of the db specific stuff.

There are two main ideas here:

1. Open up a small possibility to replace mongo by another
   db.  This means, that all direct mongo accesses should
   happen in the db submodule.  While all the rest uses an
   API defined by this submodule.

   Currently this API happens to be basicly mongo.
   Which means, that the abstraction/wrapper layer is
   extremely thin.

2. Give the rest of the app a simple and easy way to get most of
   their db needs. Which often means some simple import
   from db.util.

What does that mean?

* Never import mongo directly outside of this submodule.

* Inside this submodule you can do whatever is needed. The
  API border is exactly at the submodule layer. Nowhere
  else.

* helper functions can be moved in here. They become part
  of the db.* API

"""
