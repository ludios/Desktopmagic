from __future__ import print_function

import os
try:
	# Needed for Python 2.6 compatibility
	import unittest2 as unittest
except ImportError:
	import unittest
import tempfile

from desktopmagic.screengrab_win32 import getDisplayRects, saveRectToBmp, getRectAsImage, GrabFailed

try:
	# Pillow or PIL
	from PIL import Image
except ImportError:
	try:
		# some old PIL installations
		import Image
	except ImportError:
		Image = None


class GetDisplayRectsTest(unittest.TestCase):
	"""
	Tests for L{getDisplayRects}
	"""
	def test_getDisplayRectsReturnsList(self):
		"""
		L{getDisplayRects} returns a list of length >= 1 with a tuple containing 4 integers,
		representing the geometry of each display.
		"""
		regions = getDisplayRects()
		##print("Display rects are:", regions)
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
		print("Open taskmgr.exe to make sure I'm not leaking memory right now.")
		for i in xrange(100000):
			getDisplayRects()



class RectTests(unittest.TestCase):
	def _tryUnlink(self, fname):
		try:
			os.unlink(fname)
		except OSError:
			pass


	def test_workingCase(self):
		if not Image:
			self.skipTest("No PIL or Pillow")

		fname = tempfile.mktemp()
		self.addCleanup(self._tryUnlink, fname)
		saveRectToBmp(fname, rect=(0, 0, 200, 100))
		with open(fname, "rb") as f:
			im = Image.open(f)
			self.assertEqual((200, 100), im.size)


	def test_invalidRect(self):
		fname = tempfile.mktemp()
		self.addCleanup(self._tryUnlink, fname)
		self.assertRaises(ValueError, lambda: saveRectToBmp(fname, rect=(100, 100, 100, 100)))
		self.assertRaises(ValueError, lambda: saveRectToBmp(fname, rect=(100, 100, 99, 100)))
		self.assertRaises(ValueError, lambda: saveRectToBmp(fname, rect=(100, 100, 100, 99)))
		self.assertRaises(ValueError, lambda: saveRectToBmp(fname, rect=(100, 100, 100, None)))
		self.assertRaises(ValueError, lambda: saveRectToBmp(fname, rect=(100, 100, "100", None)))
		self.assertRaises(ValueError, lambda: saveRectToBmp(fname, rect=(100.0, 100, 101, 101)))
		self.assertRaises(ValueError, lambda: saveRectToBmp(fname, rect=(100, 100, 101, 101.0)))
		self.assertRaises(ValueError, lambda: saveRectToBmp(fname, rect=(100, 100, 200, 200, 200)))
		self.assertRaises(TypeError, lambda: saveRectToBmp(fname, rect=None))
		self.assertRaises(TypeError, lambda: getRectAsImage(rect=None))


	def test_1x1SizeRect(self):
		if not Image:
			self.skipTest("No PIL or Pillow")

		fname = tempfile.mktemp() + '.bmp'
		fnamePng = tempfile.mktemp() + '.png'
		self.addCleanup(self._tryUnlink, fname)
		self.addCleanup(self._tryUnlink, fnamePng)
		saveRectToBmp(fname, rect=(100, 100, 101, 101))

		with open(fname, "rb") as f:
			im = Image.open(f)
			self.assertEqual((1, 1), im.size)

		im = getRectAsImage(rect=(100, 100, 101, 101))
		self.assertEqual((1, 1), im.size)
		im.save(fnamePng, format='png')

		with open(fnamePng, "rb") as f:
			im = Image.open(f)
			self.assertEqual((1, 1), im.size)


	def test_rectTooBig(self):
		fname = tempfile.mktemp()
		self.addCleanup(self._tryUnlink, fname)
		# Note that 26000x26000 is big enough to fail it on my system
		self.assertRaises(GrabFailed, lambda: saveRectToBmp(fname, rect=(0, 0, 2600000, 2600000)))
		self.assertRaises(GrabFailed, lambda: saveRectToBmp(fname, rect=(0, 0, 2600000, 260000000000000000)))
