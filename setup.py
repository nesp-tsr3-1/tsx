import os
from setuptools import setup

setup(
	name='nesp',
	version='0.2',
	description='NESP',
	author='Hoang Anh Nguyen',
	author_email='hoangnguyen177@gmail.com',
	url='https://github.com/nesp-tsr/nesp',
	packages=[
		'nesp',
		'nesp.api',
		'nesp.db',
		'twisted.plugins'
	],
	entry_points={
		'console_scripts': [
			'nespdbimport = nesp.importer:main'
		]
	},
	package_data={
		'twisted': ['plugins/*',]
	},
	data_files=[
		('/opt/nesp/conf', ['nesp.conf.example']),
		# The following breaks outside of Linux, so instead added I instructions to copy manually
		# (installing init scripts doesn't belong in a Python install script anyway, it should go
		# in an OS package e.g. .deb for Ubuntu)
		# ('/etc/init.d', ['etc/init.d/nespapi']),
	],
	zip_safe=False,
	install_requires=[
		"Flask>=0.12.2",
		"Flask-Cors>=3.0.3",
		"MySQL-python>=1.2.5",
		"openpyxl>=2.4.9",
		"pyproj>=1.9.5.1",
		"python-dateutil>=2.6.1",
		"SQLAlchemy>=1.1.14",
		"GeoAlchemy2>=0.4.0",
		"pytz>=2017.3",
		"Shapely>=1.6.2.post1",
		"tzlocal>=1.4",
		"tqdm>=4.19.4"
	]
)

print """

NOTES:

The following native packages are required:

	libgeos-dev (Ubuntu) / geos-devel (centos)

To install as a Linux service:

	sudo cp etc/init.d/nespapi /etc/init.d/

Example configuration has been installed to /opt/nesp/conf/nesp.conf.example.
Copy this to 'nesp.conf' and update configuration.

"""
