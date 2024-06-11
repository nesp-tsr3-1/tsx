#!/bin/bash

set -e

mysql <<EOF
DROP DATABASE IF EXISTS tsx_fresh;
CREATE DATABASE tsx_fresh;
EOF

mysql tsx_fresh < db/sql/create.sql

sqlacodegen --options nobidi mysql+mysqlconnector://root@localhost/tsx_fresh | sed 's/\[Any\]/[str]/g' > tsx/db/models.py
