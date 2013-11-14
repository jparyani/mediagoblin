.. MediaGoblin Documentation

   Written in 2011, 2012 by MediaGoblin contributors

   To the extent possible under law, the author(s) have dedicated all
   copyright and related and neighboring rights to this software to
   the public domain worldwide. This software is distributed without
   any warranty.

   You should have received a copy of the CC0 Public Domain
   Dedication along with this software. If not, see
   <http://creativecommons.org/publicdomain/zero/1.0/>.

==================
Uploading an Image
==================

You must have fully authenticated with oauth to upload an image. 

The endpoint is: ``/api/user/<username>/uploads/`` (POST endpoint)

There are four GET parameters available to use, if they're not specified the defaults (listed below) will be used, the parameters are:

+-------------+-----------+---------------------+--------------------+
| Parameter   | Required  | Default             | Example            |
+=============+===========+=====================+====================+
| qqfile      | No        | unknown             | my_picture.jpg     |
+-------------+-----------+---------------------+--------------------+
| title       | No        | <qqfile>            | My Picture!        |
+-------------+-----------+---------------------+--------------------+
| description | No        | None                | My awesome picture |
+-------------+-----------+---------------------+--------------------+
| licence     | No        | All rights reserved | CC BY-SA 3.0       |
+-------------+-----------+---------------------+--------------------+

*Note: licence is not part of the pump.io spec and is a GNU MediaGoblin specific parameter*

Example URL (with parameters): /api/user/tsyesika/uploads/?qqfile=river.jpg&title=The%20River&description=The%20river%20that%20I%20use%20to%20visit%20as%20a%20child%20licence=CC%20BY-SA%203.0

Submit the binary image data in the POST parameter.

