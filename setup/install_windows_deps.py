# Shapely installed via pip doesn't have GEOS dependencies
# Instead we download a custom Python wheel which does have the dependencies
# (see https://stackoverflow.com/questions/13144158/python-geos-and-shapely-on-windows-64)
from urllib import urlretrieve
from subprocess import call
import os

wheels = [
	'https://download.lfd.uci.edu/pythonlibs/l8ulg3xw/GDAL-2.2.4-cp27-cp27m-win_amd64.whl',
	'https://download.lfd.uci.edu/pythonlibs/l8ulg3xw/Fiona-1.7.13-cp27-cp27m-win_amd64.whl',
	'https://download.lfd.uci.edu/pythonlibs/l8ulg3xw/Shapely-1.6.4.post1-cp27-cp27m-win_amd64.whl'
]

# Make sure we can install wheels
call(['pip', 'install', 'wheel'])

# Download wheel
print("Install custom packages")

for url in wheels:
	print("Downloading: %s" % url)
	filename = url.split("/")[-1]
	# Download it
	urlretrieve('https://download.lfd.uci.edu/pythonlibs/l8ulg3xw/Shapely-1.6.4.post1-cp27-cp27m-win_amd64.whl', filename)
	# Install it
	call(['pip', 'wheel', filename])
	# Clean up
	os.remove(filename)

print("Done")
