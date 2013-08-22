======================
 Authentication Hooks
======================

This documents the hooks that are currently available for authentication
plugins. If you need new hooks for your plugin, go ahead a submit a patch.

What hooks are available?
=========================

'authentication'
----------------

This hook just needs to return ``True`` as this is how 
the MediaGoblin app knows that an authentication plugin is enabled.


'auth_extra_validation'
-----------------------

This hook is used to provide any additional validation of the registration 
form when using ``mediagoblin.auth.tools.register_user()``. This hook runs
through all enabled auth plugins.


'auth_create_user'
------------------

This hook is used by ``mediagoblin.auth.tools.register_user()`` so plugins can
store the necessary information when creating a user. This hook runs through
all enabled auth plugins.

'auth_get_user'
---------------

This hook is used by ``mediagoblin.auth.tools.check_login_simple()``. Your
plugin should return a ``User`` object given a username.

'auth_no_pass_redirect'
-----------------------

This hook is called in ``mediagoblin.auth.views`` in both the ``login`` and 
``register`` views. This hook should return the name of your plugin, so that
if :ref:`basic_auth-chapter` is not enabled, the user will be redirected to the
correct login and registration views for your plugin.

The code assumes that it can generate a valid url given
``mediagoblin.plugins.{{ your_plugin_here }}.login`` and
``mediagoblin.plugins.{{ your_plugin_here }}.register``. This is only needed if
you will not be using the ``login`` and ``register`` views in 
``mediagoblin.auth.views``.

'auth_get_login_form'
---------------------

This hook is called in ``mediagoblin.auth.views.login()``. If you are not using
that view, then you do not need this hook. This hook should take a ``request``
object and return the ``LoginForm`` for your plugin.

'auth_get_registration_form'
----------------------------

This hook is called in ``mediagoblin.auth.views.register()``. If you are not
using that view, then you do not need this hook. This hook should take a
``request`` object and return the ``RegisterForm`` for your plugin.

'auth_gen_password_hash'
------------------------

This hook should accept a ``raw_pass`` and an ``extra_salt`` and return a
hashed password to be stored in ``User.pw_hash``.

'auth_check_password'
---------------------

This hook should accept a ``raw_pass``, a ``stored_hash``, and an ``extra_salt``.
Your plugin should then check that the ``raw_pass`` hashes to the same thing as
the ``stored_hash`` and return either ``True`` or ``False``.

'auth_fake_login_attempt'
-------------------------

This hook is called in ``mediagoblin.auth.tools.check_login_simple``. It is
called if a user is not found and should do something that takes the same amount
of time as your ``check_password`` function. This is to help prevent timining
attacks.
