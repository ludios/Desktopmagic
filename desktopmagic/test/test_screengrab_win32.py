from desktopmagic.screengrab_win32 import getDisplayRects

import unittest

class GetDisplayRectsTest(unittest.TestCase):
	"""
	Tests for L{getDisplayRects}
	"""
	def test_getDisplayRectsReturnsList(self):
		"""
		L{getDisplayRects} returns a list of length >= 1 with a tuple containing 4 integers,
		representing the dimensions ??? of each monitor.
		"""
		regions = getDisplayRects()
		print "Display rects are:", regions
		self.assertIsInstance(regions, list)
		for region in regions:
			self.assertIsInstance(region, tuple)
			for num in region:
				self.assertIsInstance(num, int)


	def disabled_test_getDisplayRectsDoesNotLeak(self):
		"""
		Calling L{getDisplayRects} 100,000 times does not leak memory (you'll have to
		open taskmgr to make sure.)

		Disabled because Ivan manually confirmed that it does not leak.
		"""
		print "Open taskmgr.exe to make sure I'm not leaking memory right now."
		for i in xrange(100000):
			getDisplayRects()


# TODO: test this case that throws an exception because coords are too big
#	im_25600 = getRectAsImage((0, 0, 25600, 25600))
#	im_25600.save('screencapture_25600_25600.png', format='png')
