.. MediaGoblin Documentation

   Written in 2011, 2012 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

==============
Authentication
==============

GNU MediaGoblin uses OAuth1 to authenticate requests to the API. There are many
libraries out there for OAuth1, you're likely not going to have to do much. There
is a library for the GNU MediaGoblin called `PyPump <https://github.com/xray7224/PyPump>`_.
We are not using OAuth2 as we want to stay completely compatable with GNU MediaGoblin.


We use :doc:`client_register` to get the client ID and secret.

Endpoints
---------

These are the endpoints you need to use for the oauth requests:

`/oauth/request_token` is for getting the request token.

`/oauth/authorize` is to send the user to to authorize your application.

`/oauth/access_token` is for getting the access token to use in requests.

