import pytest
import configparser
import tempfile
import os
import tsx.config
import mysql.connector
import shutil
import tsx.db.connect
from tsx.api.util import db_session
from contextlib import contextmanager
from sqlalchemy.orm import close_all_sessions

from subprocess import Popen, PIPE, STDOUT

# Note to self: pytest fixtures automatically become available to tests
# based on the test function having an argument that matches the name of
# the fixture function

@pytest.fixture(scope="function")
def db_name(request):
	"""
	Return the name of a temporary database that may be created for the current test
	"""

	# Database name based on current test
	return 'tsx_%s' % request.node.name

@pytest.fixture(scope="function")
def output_dir(request):
	"""
	Return the name of an newly-created output directory based on the current test.
	If the directory already exists, it will be deleted and recreated.
	The directory is *not* automatically deleted after the test.
	"""
	path = os.path.join("tests", "output", request.node.name)
	if os.path.exists(path):
		shutil.rmtree(path)
	os.makedirs(path)
	return path


@pytest.fixture(scope="function")
def data_dir(request, custom_config_file):
	path = os.path.join("tests", "tmp-data", request.node.name)
	if os.path.exists(path):
		shutil.rmtree(path)
	os.makedirs(path)

	with modify_config(custom_config_file) as config:
		config.set('global', 'data_dir', path)

	return path

@pytest.fixture(scope="function")
def custom_config_file():
	# Create config file with database name set
	config_file = tempfile.NamedTemporaryFile(
		suffix='.conf',
		prefix='tsx',
		delete=False)

	with open('tsx.conf.test', 'r') as src:
		with open(config_file.name, 'w') as dest:
			dest.write(src.read())

	# Set TSX_CONFIG environment for subprocesses to use
	os.environ['TSX_CONFIG'] = config_file.name

	tsx.config.reload()

	yield config_file.name

	# Remove temporary config file
	os.remove(config_file.name)

@contextmanager
def modify_config(path):
	config = configparser.ConfigParser()
	config.read(path)
	yield config
	with open(path, 'w') as f:
		config.write(f)
	tsx.config.reload()

@pytest.fixture(scope="function")
def fresh_database(db_name, custom_config_file):
	"""
	Return a function for connecting to a temporary database for the current test.
	The temporary database is initialised with the TSX schema using db/sql/create.sql and db/sql/init.sql.
	A configuration file is created and environment variable is set so that TSX scripts will use the temporary database.
	"""

	init_sql = [
		"""DROP DATABASE IF EXISTS %s""" % db_name,
		"""CREATE DATABASE %s""" % db_name,
		"""USE %s""" % db_name
	]

	for filename in ['db/sql/create.sql', 'db/sql/init.sql']:
		with open(filename, 'r') as f:
			init_sql.append(f.read())

	p = Popen(['mysql'], text=True, stdin=PIPE)
	p.communicate(input = ';\n'.join(init_sql))

	# Create config file with database name set
	with modify_config(custom_config_file) as config:
		config.set('database', 'name', db_name)

	tsx.db.connect.reload_config(db_session)

	# Run test
	yield get_connection_maker(config)

	close_all_sessions()

	# Clean up
	p = Popen(['mysql'], text=True, stdin=PIPE)
	p.communicate(input = """DROP DATABASE %s;\n""" % db_name)

# Takes a configuration file and returns a function that provides a database connection
def get_connection_maker(config):
	database_config = "database"
	db_type = config.get(database_config, "type").strip()
	assert(db_type == "mysql+mysqlconnector")

	host = config.get(database_config, "host").strip()
	user = config.get(database_config, "username").strip()
	password = config.get(database_config, "password").strip()
	database = config.get(database_config, "name").strip()

	def get_connection():
		return mysql.connector.connect(
			user=user,
			password=password,
			host=host,
			database=database,
			use_pure=True
		)

	return get_connection
