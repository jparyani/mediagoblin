# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
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

from mediagoblin.tools.text import tag_length_validator
from mediagoblin.tools.translate import fake_ugettext_passthrough as _
from mediagoblin.tools.licenses import licenses_as_choices


class SubmitStartForm(wtforms.Form):
    file = wtforms.FileField(_('File'))
    title = wtforms.TextField(
        _('Title'),
        [wtforms.validators.Length(min=0, max=500)])
    description = wtforms.TextAreaField(
        _('Description of this work'),
        description=_("""You can use
                      <a href="http://daringfireball.net/projects/markdown/basics">
                      Markdown</a> for formatting."""))
    tags = wtforms.TextField(
        _('Tags'),
        [tag_length_validator],
        description=_(
          "Separate tags by commas."))
    license = wtforms.SelectField(
        _('License'),
        [wtforms.validators.Optional(),],
        choices=licenses_as_choices())

class AddCollectionForm(wtforms.Form):
    title = wtforms.TextField(
        _('Title'),
        [wtforms.validators.Length(min=0, max=500), wtforms.validators.Required()])
    description = wtforms.TextAreaField(
        _('Description of this collection'),
        description=_("""You can use
                      <a href="http://daringfireball.net/projects/markdown/basics">
                      Markdown</a> for formatting."""))
