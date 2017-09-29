SatelitoVido
============

*Goes through large amounts of satellite ocean imagery looking for
something interesting.*

Intent
------

Satellite imagery is amazing. It makes it so easy to see things that just
a short time ago could only be imagined. The only problem? There's so much
of it. A person could spend days downloading large image files and looking
through them for items of interest. Wouldn't it be nice if there were a
utility that'd help do that? That's exactly what this project does.

How To Use It
-------------

It's a Python script with dependencies on OpenCV, NumPy, and SimpleJSON.
Within most Python environments something like:

.. code-block:: shell

    pip install opencv-contrib-python numpy simplejson

will make this happen for you.

It requires a SkyWatch API key to get access to satellite data (contact
info@skywatch.co to get yours). Help on using it is built in. Type

.. code-block:: shell

    ./SatelitoVido.py --help

in the same folder in which it is installed to get the full rundown on
how to make it work.

