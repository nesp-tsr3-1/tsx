#!/bin/bash

# Create tsx database and user
sudo mysql <<EOF
  CREATE USER 'tsx'@'%' IDENTIFIED BY 'tsx';
  CREATE DATABASE tsx;
  GRANT ALL PRIVILEGES ON tsx.* TO 'tsx'@'%';
EOF

# Initialize database
sudo mysql tsx < data/sql/create.sql
sudo mysql tsx < data/sql/init.sql
