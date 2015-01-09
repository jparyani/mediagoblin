.. MediaGoblin Documentation

   Written in 2015 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

==================
API Authentication
==================

.. contents:: Sections
   :local:

Registering a Client
====================

To use the GNU MediaGoblin API you need to use the dynamic client registration. This has been adapted from the `OpenID specification <https://openid.net/specs/openid-connect-registration-1_0.html>`_, this is the only part of OpenID that is being used to serve the purpose to provide the client registration which is used in OAuth.

The endpoint is ``/api/client/register``

The parameters are:

type
    **required** - This must be either *client_associate* (for new registration) or *client_update*

client_id
    **update only** - This should only be used updating client information, this is the client_id given when you register

client_secret
    **update only** - This should only be used updating client information, this is the client_secret given when you register

contacts
    **optional** - This a space separated list of email addresses to contact of people responsible for the client

application_type
    **required** - This is the type of client you are making, this must be either *web* or *native*

application_name
    **optional** - This is the name of your client

logo_uri
    **optional** - This is a URI of the logo image for your client

redirect_uri
    **optional** - This is a space separated list of pre-registered URLs for use at the Authentication Server


Response
^^^^^^^^

You will get back a response:

client_id
    This identifies a client

client_secret
    This is the secret.

expires_at
    This is time that the client credentials expire. If this is 0 the client registration does not expire.

Examples
--------

Register Client
^^^^^^^^^^^^^^^

To register a client for the first time, this is the minimum you must supply::

    {
        "type": "client_associate",
        "application_type": "native"
    }

A Response will look like::

    {
        "client_secret": "hJtfhaQzgKerlLVdaeRAgmbcstSOBLRfgOinMxBCHcb",
        "expires_at": 0,
        "client_id": "vwljdhUMhhNbdKizpjZlxv"
    }


Updating Client
^^^^^^^^^^^^^^^

Using the response we got above we can update the information and add new information we may have opted not to supply::

    {
        "type": "client_update",
        "client_id": "vwljdhUMhhNbdKizpjZlxv",
        "client_secret": "hJtfhaQzgKerlLVdaeRAgmbcstSOBLRfgOinMxBCHcb",
        "application_type": "web",
        "application_name": "MyClient!",
        "logo_uri": "https://myclient.org/images/my_logo.png",
        "contacts": "myemail@someprovider.com another_developer@provider.net",
    }

The response will just return back the client_id and client_secret you sent::

    {
        "client_id": "vwljdhUMhhNbdKizpjZlxv",
        "client_secret": "hJtfhaQzgKerlLVdaeRAgmbcstSOBLRfgOinMxBCHcb",
        "expires_at": 0
    }


Possible Registration Errors
----------------------------

There are a number of errors you could get back, This explains what could cause some of them:

Could not decode data
    This is caused when you have an error in the encoding of your data.

Unknown Content-Type
    You should sent a Content-Type header with when you make a request, this should be either application/json or www-form-urlencoded. This is caused when a unknown Content-Type is used.

No registration type provided
    This is when you leave out the ``type``. This should either be client_update or client_associate

Unknown application_type.
    This is when you have provided a ``type`` however this isn't one of the known types.

client_id is required to update.
    When you try and update you need to specify the client_id, this will be what you were given when you initially registered the client.

client_secret is required to update.
    When you try to update you need to specify the client_secret, this will be what you were given when you initially register the client.

Unauthorized.
    This is when you are trying to update however the client_id and/or client_secret you have submitted are incorrect.

Only set client_id for update.
    This should only be given when you update.

Only set client_secret for update.
    This should only be given when you update.

Logo URL <url> is not a valid URL
    This is when the URL specified did not meet the validation.

contacts must be a string of space-separated email addresses.
    ``contacts`` should be a string (not a list), ensure each email is separated by a space

Email <email> is not a valid email
    This is when you have submitted an invalid email address

redirect_uris must be space-separated URLs.
    ``redirect_uris`` should be a string (not a list), ensure each URL is separated by a space

URI <URI> is not a valid URI
    This is when your URI is invalid.

OAuth
=====

GNU MediaGoblin uses OAuth1 to authenticate requests to the API. There are many
libraries out there for OAuth1, you're likely not going to have to do much. There
is a library for the GNU MediaGoblin called `PyPump <https://github.com/xray7224/PyPump>`_.
We are not using OAuth2 as we want to stay completely compatible with pump.io.


Endpoints
---------

These are the endpoints you need to use for the oauth requests:

`/oauth/request_token` is for getting the request token.

`/oauth/authorize` is to send the user to to authorize your application.

`/oauth/access_token` is for getting the access token to use in requests.

