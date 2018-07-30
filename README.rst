===================================================================
Welcome to the Australian Threatened Species Index (TSX) Repository
===================================================================

For information about the Australian Threatened Species Index project, see http://www.nespthreatenedspecies.edu.au/projects/national-and-regional-monitoring-for-threatened-species

The code in this repository is responsible for data-import and pre-processing of data, and visualsation of the generated trend graphs and associated data. It does not (yet) contain the code for generating the actual trends.

Getting started with a local development environment
====================================================

1. Setup database (MySQL)
-------------------------

First create a new MySQL database.

You can call it anything but the instructions below assume it is named "tsx".

Initialise the database using the provided scripts:

.. code:: bash

	mysql tsx < data/sql/create.sql
	mysql tsx < data/sql/init.sql

Copy example configuration:

.. code:: bash

	cp tsx.conf.example tsx.conf

Then edit the ``[database]`` section in tsx.conf to match the database you just created.

2. Setup python virtual environment and install dependencies
------------------------------------------------------------

.. code:: bash

	pip install virtualenv # if you don't have virtualenv already
	virtualenv env
	source env/bin/activate
	pip install -r requirements.txt

3. Import taxa
--------------

.. code:: bash

	python -m tsx.import_taxa [path to TaxonList.xlsx]

4. Import some sample data
--------------------------

Via command line:

.. code:: bash

	python -m tsx.importer --type 1 --commit data/type-1-sample.csv

Or alternatively via web upload interface

.. code:: bash

	# Start back-end API:
	FLASK_DEBUG=1 FLASK_APP=tsx/api/api.py python -m flask run

	# Start front-end (in a separate terminal):
	cd web
	npm install
	npm run dev

5. Run processing scripts
-------------------------

.. code:: bash

	python -m tsx.process alpha_hull
	python -m tsx.process range_ultrataxon
	python -m tsx.process pseudo_absence

Or all at once:

.. code:: bash

	python -m tsx.process -c all


Deployment
==========

(TODO - more detailed instructions)

1. Setup database (see instructions for dev environment)

2. Install tsx package::

	python setup.py install

3. Edit configuration in ``/opt/tsx/conf/tsx.conf``

4. Setup as service (Linux)::

	sudo cp etc/init.d/tsxapi /etc/init.d/
	sudo service tsxapi start

5. Deploy static resources::

	# If you don't have have node/npm installed:
	#
	# sudo apt install npm nodejs
	#
	# .. or might need a more recent version ..
	#
	# sudo apt-get remove nodejs npm ## remove existing nodejs and npm packages
	# sudo apt-get install curl
	# curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -
	# sudo apt-get install -y nodejs
	#

	cd web
	npm install
	(TODO - add step to point code to REST API base URL)
	npm run build
	sudo cp -r dist/ /var/www/tsx/
	sudo chown -R www-data:www-data /var/www/tsx


Documentation
=============

Documentation can be generated using::

	cd doc
	make html
