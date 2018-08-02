import string
from glob import glob
import os
import sys

def main():
	mysql = find_mysql()
	print(mysql)
	if mysql:
		filename = sys.argv[1]
		with open(filename, 'w') as f:
			f.write("SET PATH=%%PATH%%;%s\n" % os.path.dirname(mysql))

def find_mysql():
	try:
		from ctypes import windll
	except:
		# Not windows, just assume mysql is on path
		return None

	# Windows
	for drive in all_drives():
		matches = glob('%s:\\Program Files*\\MySQL\\*\\bin\\mysql.exe' % drive)
		if matches:
			return matches[0]
		matches = glob('%s:\\MySQL\\bin\\mysql.exe' % drive)
		if matches:
			return matches[0]
	raise Exception("mysql not found")

def all_drives():
	from ctypes import windll
	bitmask = windll.kernel32.GetLogicalDrives()
	return [letter for (i, letter) in enumerate(string.uppercase) if (bitmask >> i) & 1]

if __name__ == '__main__':
	main()
