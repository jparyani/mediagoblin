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

from mediagoblin.util import fake_ugettext_passthrough as _


class MediaCommentForm(wtforms.Form):
    comment_content = wtforms.TextAreaField(
        _('Comment'),
        [wtforms.validators.Required()])


class ConfirmDeleteForm(wtforms.Form):
    confirm = wtforms.RadioField('Confirm',
                                 default='False',
                                 choices=[('False', 'No, I made a mistake!'),
                                          ('True', 'Yes, delete it!')])
