from __future__ import print_function

from desktopmagic.screengrab_win32 import getDisplayRects

import time

def main():
	print("""\
This program constantly polls your display rect information and prints
it when it changes.

This can be used to make sure getDisplayRects is free from desync bugs
that occur during monitor configuration changes.
""")
	lastRects = None
	count = 0
	start = time.time()
	while True:
		if count != 0 and count % 1000 == 0:
			end = time.time()
			##print(end - start, "for 1000 calls")
			start = time.time()

		rects = getDisplayRects()
		if rects != lastRects:
			print(rects)
			lastRects = rects

		count += 1


if __name__ == '__main__':
	main()
