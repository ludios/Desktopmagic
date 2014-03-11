from __future__ import print_function

from desktopmagic.screengrab_win32 import getVirtualScreenRect

import time

def main():
	print("""\
This program constantly polls your virtual screen rect information and
prints it when it changes.

This can be used to make sure getVirtualScreenRect is free from desync
bugs that occur during monitor configuration changes.
""")
	lastRect = None
	count = 0
	start = time.time()
	while True:
		if count != 0 and count % 1000 == 0:
			end = time.time()
			##print(end - start, "for 1000 calls")
			start = time.time()

		rect = getVirtualScreenRect()
		if rect != lastRect:
			print(rect)
			lastRect = rect

		count += 1


if __name__ == '__main__':
	main()
