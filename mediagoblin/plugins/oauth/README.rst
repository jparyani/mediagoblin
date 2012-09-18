==============
 OAuth plugin
==============

The OAuth plugin enables third party web applications to authenticate as one or
more GNU MediaGoblin users in a safe way in order retrieve, create and update
content stored on the GNU MediaGoblin instance.

The OAuth plugin is based on the `oauth v2.25 draft`_ and is pointing by using
the ``oauthlib.oauth2.draft25.WebApplicationClient`` from oauthlib_ to a
mediagoblin instance and building the OAuth 2 provider logic around the client.

There are surely some aspects of the OAuth v2.25 draft that haven't made it
into this plugin due to the technique used to develop it.

.. _`oauth v2.25 draft`: http://tools.ietf.org/html/draft-ietf-oauth-v2-25
.. _oauthlib: http://pypi.python.org/pypi/oauthlib


Set up the OAuth plugin
=======================

1. Add the following to your MediaGoblin .ini file in the ``[plugins]`` section::

    [[mediagoblin.plugins.oauth]]

2. Run::

        gmg dbupdate

   in order to create and apply migrations to any database tables that the
   plugin requires.

.. note::
    This only enables the OAuth plugin. To be able to let clients fetch data
    from the MediaGoblin instance you should also enable the API plugin or some
    other plugin that supports authenticating with OAuth credentials.


Authenticate against GNU MediaGoblin
====================================

.. note::
    As mentioned in `capabilities`_ GNU MediaGoblin currently only supports the
    `Authorization Code Grant`_ procedure for obtaining an OAuth access token.

Authorization Code Grant
------------------------

.. note::
    As mentioned in `incapabilities`_ GNU MediaGoblin currently does not
    support `client registration`_

The `authorization code grant`_ works in the following way:

`Definitions`

    Authorization server
        The GNU MediaGoblin instance
    Resource server
        Also the GNU MediaGoblin instance ;)
    Client
        The web application intended to use the data
    Redirect uri
        An URI pointing to a page controlled by the *client*
    Resource owner
        The GNU MediaGoblin user who's resources the client requests access to
    User agent
        Commonly the GNU MediaGoblin user's web browser
    Authorization code
        An intermediate token that is exchanged for an *access token*
    Access token
        A secret token that the *client* uses to authenticate itself agains the
        *resource server* as a specific *resource owner*.


Brief description of the procedure
++++++++++++++++++++++++++++++++++

1. The *client* requests an *authorization code* from the *authorization
   server* by redirecting the *user agent* to the `Authorization Endpoint`_.
   Which parameters should be included in the redirect are covered later in
   this document.
2. The *authorization server* authenticates the *resource owner* and redirects
   the *user agent* back to the *redirect uri* (covered later in this
   document).
3. The *client* receives the request from the *user agent*, attached is the
   *authorization code*.
4. The *client* requests an *access token* from the *authorization server*
5. \?\?\?\?\?
6. Profit!


Detailed description of the procedure
+++++++++++++++++++++++++++++++++++++

TBD, in the meantime here is a proof-of-concept GNU MediaGoblin client:

https://github.com/jwandborg/omgmg/

and here are some detailed descriptions from other OAuth 2
providers:

- https://developers.google.com/accounts/docs/OAuth2WebServer
- https://developers.facebook.com/docs/authentication/server-side/ (


Capabilities
============

- `Authorization endpoint`_ - Located at ``/oauth/authorize``
- `Token endpoint`_ - Located at ``/oauth/access_token``
- `Authorization Code Grant`_

.. _`Authorization endpoint`: http://tools.ietf.org/html/draft-ietf-oauth-v2-25#section-3.1
.. _`Token endpoint`: http://tools.ietf.org/html/draft-ietf-oauth-v2-25#section-3.2
.. _`Authorization Code Grant`: http://tools.ietf.org/html/draft-ietf-oauth-v2-25#section-4.1

Incapabilities
==============

- `Client Registration`_ - `planned feature
  <http://issues.mediagoblin.org/ticket/497>`_
- `Access Token Scope`_
- `Implicit Grant`_
- ...

.. _`Client Registration`: http://tools.ietf.org/html/draft-ietf-oauth-v2-25#section-2
.. _`Access Token Scope`: http://tools.ietf.org/html/draft-ietf-oauth-v2-25#section-3.3
.. _`Implicit Grant`: http://tools.ietf.org/html/draft-ietf-oauth-v2-25#section-4.2
