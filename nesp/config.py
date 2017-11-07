"""
Provides global configuration shared across the NESP project

Configuration is loaded from the following sources in present (highest precedence first):
	* ``nesp.conf`` in the current directory
	* the path in the ``NESP_CONFIG`` environment variable
	* ``/opt/nesp/conf/nesp.conf``

To read a config value, use::

	nesp.config.get(section, option)

The underlying ConfigParser instance can be accessed as ``nesp.config.config``.
See the standard Python ConfigParser documentation for further details.
"""

import ConfigParser
import os
import errno

config = ConfigParser.SafeConfigParser()
config.read(["nesp.conf", os.environ.get("NESP_CONFIG", ""), "/opt/nesp/conf/nesp.conf"])

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
	Get a path of subdirectory within the main NESP data directory, e.g::

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
