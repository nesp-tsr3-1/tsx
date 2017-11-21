=========================
Developer information
=========================

Generating SQLAlchemy Models
============================

SQLAlchemy models for the database are found in ``nesp/db/models.py``

This file is generated directly from the database, using the `sqlacodegen` tool::

   sqlacodegen --noinflect mysql://root@localhost/nesp > nesp/db/models.py

