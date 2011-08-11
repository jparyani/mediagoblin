=========================================
 Design Document: GNU MediaGoblin vision
=========================================

.. Note::

   When we get a wiki, this will get moved there.  It's here for now
   mostly because we didn't have a better place for it.

.. Note::

   By the time you read this, it's very likely it'll be out of date.


This document attempts to describe the envisioned workflow of GNU
MediaGoblin, from a structural standpoint.  For now, *nothing* in this
document is probably the eventual, final way that things will work.
Eventually as things come to exist, this document will hopefully be
refactored to describe how things *do* work.

This documented on hopes, dreams, rainbows, and unicorns.  And it will
come to fulfillment through a lot of hard work.  Your hard work and my
hard work.


Look and feel
=============

Default look and feel
---------------------

Mairin Duffy made mockups for something called Design Hub.  That
project did a number of things differently than the way we intend to
go, but it's probably a good idea to steal a good number of ideas from
here.

http://mairin.wordpress.com/2010/03/09/another-design-hub-mockup/


User profile mockup
-------------------

Here's an ascii art mockup on how things might look for a user's page::

      _____
     |_( )_|   USER NAME
     |  |  |
     |_/_\_|
    
        Recent artwork:
       ___________________       ___________________________
      |  ___   ___   ___  |     |_About_User_Name___________|
      | |pic| |pic| |pic| |     |                           |
      | |___| |___| |___| |     | Some sort of self-        |
      |  ___   ___   ___  |     | description probably goes |
    < | |pic| |pic| |pic| | >   | here                      |
      | |___| |___| |___| |     |                           |
      |  ___   ___   ___  |     |                           |
      | |pic| |pic| |pic| |     |                           |
      | |___| |___| |___| |     |                           |
      |___________________|     |___________________________|
    
                                 ___________________________ 
        Recent favorites:       |_Recent_activity___________|
       ___________________      | New picture: DragonFace   |
      |  ___   ___   ___  |     |                4/2/2010   |
      | |pic| |pic| |pic| |     |---------------------------|
      | |___| |___| |___| |     | Sup yall this is some kind|
      |  ___   ___   ___  |     | of mini blogpost.  Maybe  |
    < | |pic| |pic| |pic| | >   | the interface will allow  |
      | |___| |___| |___| |     | for this?                 |
      |  ___   ___   ___  |     |___________________________|
      | |pic| |pic| |pic| |     
      | |___| |___| |___| |      ___________________________ 
      |___________________|     |_External_comments_here____|
                                | Dang!  This stuff rocks   |
                                |          - Joe 4/2/2010   |
                                |---------------------------|
                                | Nice job on the dragon    |
                                |         - Morgan 4/2/2010 |
                                '---------------------------'

So there's this type of interface that puts a lot of different types
of info on the same screen.  I'm not sure that I like it.  It's
possible we'll go with something much more minimalist.  Maybe we'll go
with something "tabbed" the way statusnet / http://identi.ca is on
user pages.

It's possible that we could support multiple profile styles here,
and you could load whatever profile style you want as set by user
preferences?


Uploading mockup
----------------

Here's an uploading mockup::

     Upload an image
    
     [ Title                                 ]
    
     Upload: [                      ] [Browse]
      ___________________________________________
     |                                           |
     |                                           |
     |                   o0O                     |
     |                  o   '                    |
     |                   o_.'                    |
     |                                           |
     |             Uploading... OK               | <-,
     |              Resizing... OK               |   |
     |                                           | Area replaced w/ resized
     |                                           | image when done
     |___________________________________________|
              ________________
     License |_CC BY-SA_____|V|
      ___________________________________________
     | Description goes here.                    |
     | You can type it up in here and everything |
     | and it'll show up under the image.        |
     |                                           |
     | Possibly we should allow some kind of     |
     | markup... maybe markdown?                 |
     '___________________________________________'
    
      __________________________________________
     |> Advanced                                |
      ------------------------------------------


Customizability
---------------

General site theming customizability is pretty easy!  Since we're
using `Jinja <http://jinja.pocoo.org/docs/>`_ we can just set up
user-overriding directories.

We'll also figure out some sort of way to provide theming "packages",
eventually.


