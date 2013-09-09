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

from mediagoblin.tools.text import tag_length_validator, TOO_LONG_TAG_WARNING
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _
from mediagoblin.tools.licenses import licenses_as_choices

class BlogPostEditForm(wtforms.Form):
    title = wtforms.TextField(_('Title'),
		[wtforms.validators.Length(min=0, max=500)])
    description = wtforms.TextAreaField(_('Description'))
    tags = wtforms.TextField(_('Tags'), [tag_length_validator], 
		description="Seperate tags by commas.")
    license = wtforms.SelectField(_('License'), 
		[wtforms.validators.Optional(),], choices=licenses_as_choices())

class BlogEditForm(wtforms.Form):
    title = wtforms.TextField(_('Title'),
		[wtforms.validators.Length(min=0, max=500)])
    description = wtforms.TextAreaField(_('Description'))
    

class ConfirmDeleteForm(wtforms.Form):
    confirm = wtforms.BooleanField(
        _('I am sure I want to delete this'))
    

    
    
    
    
