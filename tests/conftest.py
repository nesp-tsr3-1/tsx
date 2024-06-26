import pytest
import configparser
import tempfile
import os
import tsx.config
import mysql.connector

from subprocess import Popen, PIPE, STDOUT


@pytest.fixture(scope="function")
def db_name(request):
	# Database name based on current test
	return 'tsx_%s' % request.node.name

@pytest.fixture(scope="function")
def fresh_database(db_name):
	# Create database
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

	config = configparser.ConfigParser()
	config.read('tsx.conf.test')
	config.set('database', 'name', db_name)

	# Create config file with database name set
	config_file = tempfile.NamedTemporaryFile(
		suffix='.conf',
		prefix='tsx',
		delete=False)

	with open(config_file.name, 'w') as f:
		config.write(f)

	# Set TSX_CONFIG environment for subprocesses to use
	os.environ['TSX_CONFIG'] = config_file.name

	# Run test
	yield get_connection_maker(config)

	# Clean up
	p = Popen(['mysql'], text=True, stdin=PIPE)
	p.communicate(input = """DROP DATABASE %s""" % db_name)
	os.remove(config_file.name)

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
