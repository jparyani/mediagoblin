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
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _

class MediaCommentForm(wtforms.Form):
    comment_content = wtforms.TextAreaField(
        _('Comment'),
        [wtforms.validators.Required()],
        description=_(u'You can use '
                      u'<a href="http://daringfireball.net/projects/markdown/basics">'
                      u'Markdown</a> for formatting.'))

class ConfirmDeleteForm(wtforms.Form):
    confirm = wtforms.BooleanField(
        _('I am sure I want to delete this'))

class ConfirmCollectionItemRemoveForm(wtforms.Form):
    confirm = wtforms.BooleanField(
        _('I am sure I want to remove this item from the collection'))

class MediaCollectForm(wtforms.Form):
    collection = QuerySelectField(
        _('Collection'),
        allow_blank=True, blank_text=_('-- Select --'), get_label='title',)
    note = wtforms.TextAreaField(
        _('Include a note'),
        [wtforms.validators.Optional()],)
    collection_title = wtforms.TextField(
        _('Title'),
        [wtforms.validators.Length(min=0, max=500)])
    collection_description = wtforms.TextAreaField(
        _('Description of this collection'),
        description=_("""You can use
                      <a href="http://daringfireball.net/projects/markdown/basics">
                      Markdown</a> for formatting."""))
