import wtforms

class AuthorizeForm(wtforms.Form):
    """ Form used to authorize the request token """

    oauth_token = wtforms.HiddenField("oauth_token")
    oauth_verifier = wtforms.HiddenField("oauth_verifier")
