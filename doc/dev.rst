=========================
Developer information
=========================

Generating SQLAlchemy Models
============================

SQLAlchemy models for the database are found in ``nesp/db/models.py``

This file is generated directly from the database, using the `sqlacodegen` tool::

   sqlacodegen --noinflect mysql://root@localhost/nesp > nesp/db/models.py

Unfortunately `sqlacodegen` does not understand geometry types by default, so we need to add the line::

   from geoalchemy2 import Geometry

.. Ignore this:

.. And then replace all instances of ``NullType`` with ``Geometry``.

.. All-in-one command::

.. 	sqlacodegen --noinflect mysql://root@localhost/nesp |\
.. 	sed  's/.*import NullType/from geoalchemy2 import Geometry/' |\
.. 	sed 's/NullType/Geometry/g' \
.. 	> nesp/db/models.py
