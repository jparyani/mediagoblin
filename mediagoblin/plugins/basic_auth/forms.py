import wtforms

from mediagoblin.tools.translate import lazy_pass_to_ugettext as _
from mediagoblin.auth.tools import normalize_user_or_email_field


class RegistrationForm(wtforms.Form):
    username = wtforms.TextField(
        _('Username'),
        [wtforms.validators.Required(),
         normalize_user_or_email_field(allow_email=False)])
    password = wtforms.PasswordField(
        _('Password'),
        [wtforms.validators.Required(),
         wtforms.validators.Length(min=5, max=1024)])
    email = wtforms.TextField(
        _('Email address'),
        [wtforms.validators.Required(),
         normalize_user_or_email_field(allow_user=False)])


class LoginForm(wtforms.Form):
    username = wtforms.TextField(
        _('Username or Email'),
        [wtforms.validators.Required(),
         normalize_user_or_email_field()])
    password = wtforms.PasswordField(
        _('Password'),
        [wtforms.validators.Required(),
         wtforms.validators.Length(min=5, max=1024)])


class ForgotPassForm(wtforms.Form):
    username = wtforms.TextField(
        _('Username or email'),
        [wtforms.validators.Required(),
         normalize_user_or_email_field()])


class ChangePassForm(wtforms.Form):
    password = wtforms.PasswordField(
        'Password',
        [wtforms.validators.Required(),
         wtforms.validators.Length(min=5, max=1024)])
    userid = wtforms.HiddenField(
        '',
        [wtforms.validators.Required()])
    token = wtforms.HiddenField(
        '',
        [wtforms.validators.Required()])
