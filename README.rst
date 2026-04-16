===================================================================
Welcome to the Australian Threatened Species Index (TSX) Repository
===================================================================

For information about the Australian Threatened Species Index project, see https://tsx.org.au

The code in this repository is responsible for data import and pre-processing of data, and visualsation of the generated trend graphs and associated data.


User Guide
==========

The easiest way to learn about running the TSX workflow is to check out the User Guide at https://tsx.org.au/user-guide/

Overview
========

The TSX consists of several components

- MySQL database:
    - For storage of raw data, which is either uploaded via the data interface, or imported via the command line scripts
    - For storage for the data interface (e.g. user accounts, custodian feedback data, etc.)
    - For processing of data using SQL queries and storing the results
    - database schema is found under `db/sql/create.sql`

- Python scripts:
    - For running the TSX workflow that transforms raw data into time series
    - For importing data such as taxonomic lists and species range polygons
    - For generating trend permutations to be displayed by the TSX visualiser
    - Found in the `tsx` directory

- LPI R package (https://github.com/Zoological-Society-of-London/rlpi)
    - Developed by Zoological Society of London
    - For producing trends from time series using the Living Planet Index method
    - We maintain a fork at https://github.com/nesp-tsr3-1/rlpi for bugfixes

- API backend:
    - Implemented in Python as a Flask app
    - Backend for TSX Data Interface and TSX Visualiser
    - Code lives under `tsx/api`

- Data interface front-end (https://tsx.org.au/data)
    - Implemented using the Vue Javascript framework
    - Provides an interface for users to upload, manage and analyse datasets
    - Requires login access (data custodians can self-register)
    - Code lives under `web/data`

- TSX Visualiser (https://tsx.org.au/tsx)
    - Implemented using the Vue Javascript framework
    - A single-page application that allows users to explore a set of trend permutations
    - A separate instance is deployed for each new version of the TSX
    - Code lives under `web/tsx`

Prerequisites
=============

- MySQL 8.x
- Python 3.12+
- Node 22+
- R 3.6+
- `uv <https://docs.astral.sh/uv/>`_

Setup
=====

Clone this repository
---------------------

git clone https://github.com/nesp-tsr3-1/tsx.git


Native install vs Docker Compose
--------------------------------

There are two main options for getting a TSX development environment up and running:

1. Installing dependencies natively as per instructions below

2. Use the supplied Docker Compose configuation to automatically build containers with the necessary dependencies included. This is quicker to get up and running, but is arguably more complicated to use for development and requires some familiarity with Docker. (TODO: Docker compose instructions)


Install native packages
-----------------------

Install development libraries (Ubuntu/Debian):

.. code:: bash

 sudo apt-get update
 sudo apt-get install libgdal-dev git build-essential libharfbuzz-dev libfribidi-dev \
   libfontconfig1-dev libgit2-dev libssl-dev default-mysql-client libbz2-dev curl


Create MySQL database
---------------------

By default, the TSX software is configured to use a database called 'tsx' with a username of 'tsx' and a password of 'tsx'. This is configured in the `tsx.conf` file.

To create this database and user, connect to MySQL as root and run the following commands:

.. code:: sql

 CREATE USER 'tsx'@'%' IDENTIFIED BY 'tsx';
 CREATE DATABASE tsx;
 GRANT ALL PRIVILEGES ON tsx.* TO 'tsx'@'%';


Alternatively, you can avoid installing MySQL and instead run it via Docker (https://hub.docker.com/_/mysql/):

.. code:: bash

 docker run -d --name tsx-mysql -e MYSQL_DATABASE=tsx -e MYSQL_USER=tsx -e MYSQL_PASSWORD=tsx \
   -e MYSQL_ROOT_PASSWORD=root -p 3306:3306 mysql:8.3.0


Initialise MySQL database
--------------------------

Initialise the database using the provided scripts:

.. code:: bash

 # Native MySQL install:
 mysql -u tsx -ptsx tsx < db/sql/create.sql
 mysql -u tsx -ptsx tsx < db/sql/init.sql

 # MySQL in Docker:
 docker exec tsx-mysql mysql -u tsx -ptsx tsx < db/sql/create.sql
 docker exec tsx-mysql mysql -u tsx -ptsx tsx < db/sql/init.sql

 # Docker Compose:
 docker compose run docker compose run --rm workflow_cli
 TSX:/tsx# mysql < db/sql/create.sql
 TSX:/tsx# mysql < db/sql/init.sql

Note that if you are following the workflow user guide, you will also want to seed the database with some extra sample data found in sample-data/seed.sql

Copy example configuration
--------------------------

.. code:: bash

 cp tsx.conf.example tsx.conf

If necessary edit the ``[database]`` section in tsx.conf to match the database you just created.

Install R dependencies
------------------------

R dependencies are managed using `renv <https://rstudio.github.io/renv/articles/renv.html>`_.

Install R dependencies by running:

.. code:: bash

  Rscript -e 'renv::restore()'

Install Python dependencies
----------------------------------

Python dependencies are managed using `uv <https://docs.astral.sh/uv/>`_.

Install uv: https://docs.astral.sh/uv/getting-started/installation/

Use uv to install Python and packages:

.. code:: bash

 uv sync


Install node and Javascript dependencies
----------------------------------------

Install Javascript dependencies:

.. code:: bash

 cd web
 npm install


Run API backend
---------------

This is required for the Data Interface and/or TSX Visualiser to function

.. code:: bash

  # Native environment
  uv run ./dev-server.sh

  # Docker compose (note this also runs the Data Interface front end)
  docker compose --profile webapp up


Run Data Interface
------------------

.. code:: bash

  cd web
  npm run dev-data


Run TSX Visualiser
------------------

.. code:: bash

  cd web
  npm run dev-tsx


Note: the TSX Visualiser will not function properly until time series and trend permutations have been generated.


Docker Compose
==============

The following command will build necessary Docker containers and start a shell for running the workflow:

.. code:: bash

  docker compose run --build --rm workflow_cli

It will take a while to download the necessary packages and build the containers.

Important notes:

- When running via Docker Compose, ``tsx.conf`` must be configured with a database hostname of ``mysql``. (i.e. set ``host=mysql`` under ``[database]``)
- The project root directory is mounted to the default working directory (``/tsx/``) inside each container. In order to import your own files using the workflow, you will need to first put them within the project directory tree so that the container can see them.

To run the Data Interface and TSX Visualiser, use:

.. code:: bash

  docker compose --profile webapp up


Generate time series and permutations for sample data
=====================================================

A script is provided that will perform a full workflow run using the sample data and generate trend permutations for the TSX visualiser.

.. code:: bash

 uv run setup/test-workflow.sh

