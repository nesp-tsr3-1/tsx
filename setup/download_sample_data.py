from urllib import urlretrieve, URLopener
import ssl
from subprocess import call
import os
import zipfile

# Unfortunately NESP SSL certificate doesn't play nice with Python 2.7 on Windows. Tried hard to fix this the proper way but gave up.
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
opener = URLopener(context = ctx)

print("Downloading sample data, please wait")
filename = 'sample.zip'
opener.retrieve('https://tsx.org.au/sample.zip', filename)

print("Extracting")
zip_ref = zipfile.ZipFile(filename, 'r')
zip_ref.extractall('.')
zip_ref.close()

# Clean up
print("Clean up")
os.remove(filename)

print("Done")
