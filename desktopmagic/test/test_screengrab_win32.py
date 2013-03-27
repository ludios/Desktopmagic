from desktopmagic.screengrab_win32 import getMonitorRegions

import unittest

class GetMonitorRegionsTest(unittest.TestCase):
	"""
	Tests for L{getMonitorRegions}
	"""
	def test_getMonitorRegionsReturnsList(self):
		"""
		L{getMonitorRegions} returns a list of length >= 1 with a tuple containing 4 integers,
		representing the dimensions ??? of each monitor.
		"""
		regions = getMonitorRegions()
		print "Monitor regions are:", regions
		self.assertIsInstance(regions, list)
		for region in regions:
			self.assertIsInstance(region, tuple)
			for num in region:
				self.assertIsInstance(num, int)


	def disabled_test_getMonitorRegionsDoesNotLeak(self):
		"""
		Calling L{getMonitorRegions} 100,000 times does not leak memory (you'll have to
		open taskmgr to make sure.)

		Disabled because Ivan manually confirmed that it does not leak.
		"""
		print "Open taskmgr.exe to make sure I'm not leaking memory right now."
		for i in xrange(100000):
			getMonitorRegions()
