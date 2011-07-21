# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011 Free Software Foundation, Inc
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


import wtforms
from mediagoblin.util import tag_length_validator, TOO_LONG_TAG_WARNING


class EditForm(wtforms.Form):
    title = wtforms.TextField(
        'Title',
        [wtforms.validators.Length(min=0, max=500)])
    slug = wtforms.TextField(
        'Slug')
    description = wtforms.TextAreaField('Description of this work')
    tags = wtforms.TextField(
        'Tags',
        [tag_length_validator])

class EditProfileForm(wtforms.Form):
    bio = wtforms.TextAreaField('Bio',
        [wtforms.validators.Length(min=0, max=500)])
    url = wtforms.TextField(
        'Website',
        [wtforms.validators.Optional(),
         wtforms.validators.URL(message='Improperly formed URL')])
