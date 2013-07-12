==================
 Media Type hooks
==================

This documents the hooks that are currently available for ``media_type`` plugins.

What hooks are available?
=========================

'sniff_handler'
---------------

This hook is used by ``sniff_media`` in ``mediagoblin.media_types.__init__``.
Your media type should return its ``sniff_media`` method when this hook is
called.

.. Note::
    Your ``sniff_media`` method should return either the ``media_type`` or
    ``None``.

'get_media_type_and_manager'
----------------------------

This hook is used by ``get_media_type_and_manager`` in
``mediagoblin.media_types.__init__``. When this hook is called, your media type
plugin should check if it can handle the given extension. If so, your media
type plugin should return the media type and media manager.

('media_manager', MEDIA_TYPE)
-----------------------------

If you already know the string representing the media type of a type
of media, you can pull down the manager specifically.  Note that this
hook is not a string but a tuple of two strings, the latter being the
name of the media type.

This is used by media entries to pull down their media managers, and
so on.
