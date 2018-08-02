from urllib import urlretrieve
from subprocess import call
import os
import zipfile

print("Downloading sample data, please wait")
filename = 'sample.zip'
urlretrieve('https://nesp-dev1.coesra.org.au/sample.zip', filename)

print("Extracting")
zip_ref = zipfile.ZipFile(filename, 'r')
zip_ref.extractall('.')
zip_ref.close()

# Clean up
print("Clean up")
os.remove(filename)

print("Done")
