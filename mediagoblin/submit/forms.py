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

from mediagoblin import mg_globals
from mediagoblin.tools.text import tag_length_validator
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _
from mediagoblin.tools.licenses import licenses_as_choices


def get_submit_start_form(form, **kwargs):
    max_file_size = kwargs.get('max_file_size')
    desc = None
    if max_file_size:
        desc = _('Max file size: {0} mb'.format(max_file_size))

    class SubmitStartForm(wtforms.Form):
        file = wtforms.FileField(
            _('File'),
            description=desc)
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
        max_file_size = wtforms.HiddenField('')
        upload_limit = wtforms.HiddenField('')
        uploaded = wtforms.HiddenField('')

    return SubmitStartForm(form, **kwargs)

class AddCollectionForm(wtforms.Form):
    title = wtforms.TextField(
        _('Title'),
        [wtforms.validators.Length(min=0, max=500), wtforms.validators.Required()])
    description = wtforms.TextAreaField(
        _('Description of this collection'),
        description=_("""You can use
                      <a href="http://daringfireball.net/projects/markdown/basics">
                      Markdown</a> for formatting."""))
