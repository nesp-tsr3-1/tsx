import os
from setuptools import setup

setup(
	name='tsx',
	version='0.2',
	description='TSX',
	author='Hoang Anh Nguyen, James Watmuff',
	author_email='hoangnguyen177@gmail.com',
	url='https://github.com/nesp-tsr3-1/tsx',
	packages=[
		'tsx',
		'tsx.api',
		'tsx.db',
		'twisted.plugins'
	],
	entry_points={
		'console_scripts': [
			'tsx-import = tsx.importer:main'
		]
	},
	package_data={
		'twisted': ['plugins/*',]
	},
	data_files=[
		('/opt/tsx/conf', ['tsx.conf.example']),
		# The following breaks outside of Linux, so instead added I instructions to copy manually
		# (installing init scripts doesn't belong in a Python install script anyway, it should go
		# in an OS package e.g. .deb for Ubuntu)
		# ('/etc/init.d', ['etc/init.d/nespapi']),
	],
	zip_safe=False,
	install_requires=[
		"Twisted>=17.9.0",
		"pyOpenSSL>=17.5.0",
		"Flask>=1.1.1",
		"Flask-Cors>=3.0.6",
		"Flask-Session>=0.3.1",
		"mysql-connector",
		"openpyxl>=2.4.9",
		"pyproj>=1.9.5.1",
		"python-dateutil>=2.6.1",
		"SQLAlchemy>=1.1.14",
		"GeoAlchemy2>=0.4.0",
		"pytz>=2017.3",
		"Shapely>=1.6.2.post1",
		"tzlocal>=1.4",
		"tqdm>=4.19.4",
		"pandas>=0.21.0",
		"configparser>=3.7.4",
		"passlib>=1.7.1"
	]
)

print("""

NOTES:

The following native packages are required:

	libgeos-dev (Ubuntu) / geos-devel (centos)

To install as a Linux service:

	sudo cp etc/init.d/tsxapi /etc/init.d/

Example configuration has been installed to /opt/tsx/conf/tsx.conf.example.
Copy this to 'tsx.conf' and update configuration.

""")
