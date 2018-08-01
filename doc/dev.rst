=========================
Developer information
=========================

Generating SQLAlchemy Models
============================

SQLAlchemy models for the database are found in ``tsx/db/models.py``

This file is generated directly from the database, using the `sqlacodegen` tool::

   sqlacodegen --noinflect mysql://root@localhost/tsx > tsx/db/models.py

