from __future__ import print_function

import sys

from desktopmagic.screengrab_win32 import GrabFailed, getScreenAsImage, getDisplaysAsImages, getRectAsImage

def main():
	print("""\
This program helps you test whether screengrab_win32 has memory leaks
and other problems.  It takes a screenshot repeatedly and discards it.

Open Task Manager and make sure Physical Memory % is not ballooning.
Memory leaks might not be blamed on the python process itself (which
will show low memory usage).

Lock the workstation for a few minutes; make sure there are no leaks
and that there are no uncaught exceptions here.

Repeat above after RDPing into the workstation and minimizing RDP;
this is like disconnecting the monitor.

Change your color depth settings.  Add and remove monitors.  RDP
in at 256 colors.
""")
	while True:
		try:
			getScreenAsImage()
			print("S", end=" ")
			sys.stdout.flush()
		except GrabFailed as e:
			print(e)

		try:
			getDisplaysAsImages()
			print("D", end=" ")
			sys.stdout.flush()
		except GrabFailed as e:
			print(e)

		try:
			getRectAsImage((0, 0, 1, 1))
			print("R", end=" ")
			sys.stdout.flush()
		except GrabFailed as e:
			print(e)


if __name__ == '__main__':
	main()
