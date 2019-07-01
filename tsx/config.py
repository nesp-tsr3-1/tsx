"""
Provides global configuration shared across the TSX project

Configuration is loaded from the following sources in present (highest precedence first):
	* ``tsx.conf`` in the current directory
	* the path in the ``TSX_CONFIG`` environment variable
	* ``/opt/tsx/conf/tsx.conf``

To read a config value, use::

	tsx.config.get(section, option)

The underlying ConfigParser instance can be accessed as ``tsx.config.config``.
See the standard Python ConfigParser documentation for further details.
"""

import configparser
import os
import errno

config = configparser.SafeConfigParser()
config.read(["tsx.conf", os.environ.get("TSX_CONFIG", ""), "/opt/tsx/conf/tsx.conf"])

def get(section, option, default = None):
	"""
	Reads a config option from the given section, returning the default if the option does not exist
	"""
	try:
		return config.get(section, option)
	except:
		return default

def data_dir(path):
	"""
	Get a path of subdirectory within the main TSX data directory, e.g::

		data_dir('uploads')

	The data directory is defined by the configuration variable ``data_dir`` under the ``global`` section.

	The path will be created if it does not already exist.
	"""
	path = os.path.join(config.get("global", "data_dir"), path)

	try:
		os.makedirs(path)
	except OSError as exc:  # Python >2.5
		if exc.errno == errno.EEXIST and os.path.isdir(path):
			pass
		else:
			raise

	return path
