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
from mediagoblin.tools.translate import fake_ugettext_passthrough as _
from mediagoblin.tools.licenses import licenses_as_choices

class EditForm(wtforms.Form):
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
    slug = wtforms.TextField(
        _('Slug'),
        [wtforms.validators.Required(message=_("The slug can't be empty"))],
        description=_(
            "The title part of this media's address. "
            "You usually don't need to change this."))
    license = wtforms.SelectField(
        _('License'),
        [wtforms.validators.Optional(),],
        choices=licenses_as_choices())

class EditProfileForm(wtforms.Form):
    bio = wtforms.TextAreaField(
        _('Bio'),
        [wtforms.validators.Length(min=0, max=500)],
        description=_("""You can use
                      <a href="http://daringfireball.net/projects/markdown/basics">
                      Markdown</a> for formatting."""))
    url = wtforms.TextField(
        _('Website'),
        [wtforms.validators.Optional(),
         wtforms.validators.URL(message=_("This address contains errors"))])


class EditAccountForm(wtforms.Form):
    old_password = wtforms.PasswordField(
        _('Old password'),
        description=_(
            "Enter your old password to prove you own this account."))
    new_password = wtforms.PasswordField(
        _('New password'),
        [
            wtforms.validators.Optional(),
            wtforms.validators.Length(min=6, max=30)
        ],
        id="password")
    license_preference = wtforms.SelectField(
        _('License preference'),
        [
            wtforms.validators.Optional(),
            wtforms.validators.AnyOf([lic[0] for lic in licenses_as_choices()]),
        ],
        choices=licenses_as_choices(),
        description=_('This will be your default license on upload forms.'))
    wants_comment_notification = wtforms.BooleanField(
        label=_("Email me when others comment on my media"))


class EditAttachmentsForm(wtforms.Form):
    attachment_name = wtforms.TextField(
        'Title')
    attachment_file = wtforms.FileField(
        'File')

class EditCollectionForm(wtforms.Form):
    title = wtforms.TextField(
        _('Title'),
        [wtforms.validators.Length(min=0, max=500), wtforms.validators.Required(message=_("The title can't be empty"))])
    description = wtforms.TextAreaField(
        _('Description of this collection'),
        description=_("""You can use
                      <a href="http://daringfireball.net/projects/markdown/basics">
                      Markdown</a> for formatting."""))
    slug = wtforms.TextField(
        _('Slug'),
        [wtforms.validators.Required(message=_("The slug can't be empty"))],
        description=_(
            "The title part of this collection's address. "
            "You usually don't need to change this."))
