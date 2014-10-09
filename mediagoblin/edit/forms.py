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
from jsonschema import Draft4Validator

from mediagoblin.tools.text import tag_length_validator
from mediagoblin.tools.translate import lazy_pass_to_ugettext as _
from mediagoblin.tools.licenses import licenses_as_choices
from mediagoblin.tools.metadata import DEFAULT_SCHEMA, DEFAULT_CHECKER
from mediagoblin.auth.tools import normalize_user_or_email_field


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
        [wtforms.validators.InputRequired(message=_("The slug can't be empty"))],
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

    location = wtforms.TextField(_('Hometown'))

class EditAccountForm(wtforms.Form):
    wants_comment_notification = wtforms.BooleanField(
        description=_("Email me when others comment on my media"))
    wants_notifications = wtforms.BooleanField(
        description=_("Enable insite notifications about events."))
    license_preference = wtforms.SelectField(
        _('License preference'),
        [
            wtforms.validators.Optional(),
            wtforms.validators.AnyOf([lic[0] for lic in licenses_as_choices()]),
        ],
        choices=licenses_as_choices(),
        description=_('This will be your default license on upload forms.'))


class EditAttachmentsForm(wtforms.Form):
    attachment_name = wtforms.TextField(
        'Title')
    attachment_file = wtforms.FileField(
        'File')


class EditCollectionForm(wtforms.Form):
    title = wtforms.TextField(
        _('Title'),
        [wtforms.validators.Length(min=0, max=500), wtforms.validators.InputRequired(message=_("The title can't be empty"))])
    description = wtforms.TextAreaField(
        _('Description of this collection'),
        description=_("""You can use
                      <a href="http://daringfireball.net/projects/markdown/basics">
                      Markdown</a> for formatting."""))
    slug = wtforms.TextField(
        _('Slug'),
        [wtforms.validators.InputRequired(message=_("The slug can't be empty"))],
        description=_(
            "The title part of this collection's address. "
            "You usually don't need to change this."))


class ChangePassForm(wtforms.Form):
    old_password = wtforms.PasswordField(
        _('Old password'),
        [wtforms.validators.InputRequired()],
        description=_(
            "Enter your old password to prove you own this account."))
    new_password = wtforms.PasswordField(
        _('New password'),
        [wtforms.validators.InputRequired(),
         wtforms.validators.Length(min=6, max=30)],
        id="password")


class ChangeEmailForm(wtforms.Form):
    new_email = wtforms.TextField(
        _('New email address'),
        [wtforms.validators.InputRequired(),
         normalize_user_or_email_field(allow_user=False)])
    password = wtforms.PasswordField(
        _('Password'),
        [wtforms.validators.InputRequired()],
        description=_(
            "Enter your password to prove you own this account."))

class MetaDataValidator(object):
    """
    Custom validator which runs form data in a MetaDataForm through a jsonschema
    validator and passes errors recieved in jsonschema to wtforms.

    :param  schema              The json schema to validate the data against. By
                                default this uses the DEFAULT_SCHEMA from
                                mediagoblin.tools.metadata.
    :param  format_checker      The FormatChecker object that limits which types
                                jsonschema can recognize. By default this uses
                                DEFAULT_CHECKER from mediagoblin.tools.metadata.
    """
    def __init__(self, schema=DEFAULT_SCHEMA, format_checker=DEFAULT_CHECKER):
        self.schema = schema
        self.format_checker = format_checker

    def __call__(self, form, field):
        metadata_dict = {field.data:form.value.data}
        validator = Draft4Validator(self.schema,
                        format_checker=self.format_checker)
        errors = [e.message
            for e in validator.iter_errors(metadata_dict)]
        if len(errors) >= 1:
            raise wtforms.validators.ValidationError(
                errors.pop())

class MetaDataForm(wtforms.Form):
    identifier = wtforms.TextField(_(u'Identifier'),[MetaDataValidator()])
    value = wtforms.TextField(_(u'Value'))

class EditMetaDataForm(wtforms.Form):
    media_metadata = wtforms.FieldList(
        wtforms.FormField(MetaDataForm, ""),
    )
