# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2014 MediaGoblin contributors.  See AUTHORS.
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

from mediagoblin.db.models import Activity, Generator, User

def create_activity(verb, obj, actor, target=None):
    """
    This will create an Activity object which for the obj if possible
    and save it. The verb should be one of the following:
        add, author, create, delete, dislike, favorite, follow
        like, post, share, unfollow, unfavorite, unlike, unshare,
        update, tag.

    If none of those fit you might not want/need to create an activity for
    the object. The list is in mediagoblin.db.models.Activity.VALID_VERBS
    """
    # exception when we try and generate an activity with an unknow verb
    # could change later to allow arbitrary verbs but at the moment we'll play
    # it safe.

    if verb not in Activity.VALID_VERBS:
        raise ValueError("A invalid verb type has been supplied.")

    # This should exist as we're creating it by the migration for Generator
    generator = Generator.query.filter_by(name="GNU MediaGoblin").first()
    if generator is None:
        generator = Generator(
            name="GNU MediaGoblin",
            object_type="service"
        )
        generator.save()

    activity = Activity(verb=verb)
    activity.set_object(obj)

    if target is not None:
        activity.set_target(target)

   # If they've set it override the actor from the obj.
    activity.actor = actor.id if isinstance(actor, User) else actor

    activity.generator = generator.id
    activity.save()

    # Sigh want to do this prior to save but I can't figure a way to get
    # around relationship() not looking up object when model isn't saved.
    if activity.generate_content():
        activity.save()

    return activity
