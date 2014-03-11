"""
Robust functions for grabbing and saving screenshots on Windows.
"""

from __future__ import print_function

import ctypes
import win32gui
import win32ui
import win32con
import win32api

try:
	long
except NameError:
	# Python 3
	long = int


def checkRect(rect):
	"""
	Check C{rect} for validity.

	Raises L{ValueError} if C{rect}'s computed width or height is zero or
	negative, or if rect contains nonsense.
	"""
	try:
		left, top, right, bottom = rect
	except ValueError:
		raise ValueError("%r is not a valid rect; must contain 4 ints" % (rect,))
	if not all(isinstance(x, (int, long)) for x in rect):
		raise ValueError("%r is not a valid rect; must contain 4 ints" % (rect,))
	width = right - left
	height = bottom - top
	if width <= 0 or height <= 0:
		raise ValueError("%r is not a valid rect; width and height must not be "
			"zero or negative" % (rect,))


class RectFailed(Exception):
	"""
	Could not get information about the virtual screen or a display.
	"""



def getVirtualScreenRect():
	"""
	Returns a tuple containing (
		the x-coordinate of the upper-left corner of the virtual screen,
		the y-coordinate of the upper-left corner of the virtual screen,
		the x-coordinate of the lower-right corner of the virtual screen,
		the y-coordinate of the lower-right corner of the virtual screen
	)

	Note that both x and y coordinates may be negative; the (0, 0) origin is
	determined by the top-left corner of the main display (not necessarily
	Display 1).

	Internally, this grabs the geometry from Windows at least twice to avoid
	getting bad geometry during changes to the display configuration.

	Raises L{RectFailed} if the geometry cannot be retrieved, though
	this failure mode has never been observed.
	"""
	# Note that one iteration of the loop takes about 2us on a Q6600.
	tries = 150
	lastRect = None
	for _ in range(tries):
		# Get dimensions of the entire virtual screen.  Note that left/top may be negative.
		# Any of these may return nonsense numbers during display configuration
		# changes (not just "desync" between our calls, but numbers that make little
		# sense, as if some Windows state doesn't change synchronously.)
		# This is why we get them at least twice.
		left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
		top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
		width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
		height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)

		right = left + width
		bottom = top + height

		rect = (left, top, right, bottom)
		try:
			checkRect(rect)
		except ValueError:
			lastRect = None
		else:
			if rect == lastRect:
				return rect
			else:
				lastRect = rect

	raise RectFailed("Could not get stable rect information after %d tries; "
		"last was %r." % (tries, lastRect))


def getDisplayRects():
	"""
	Returns a list containing tuples with the coordinates of each display that is
	making up the virtual screen.  This list is ordered by display number.

	Each tuple in the list is (left, top, right, bottom), specifically (
		the x-coordinate of the upper-left corner of the display,
		the y-coordinate of the upper-left corner of the display,
		the x-coordinate of the lower-right corner of the display,
		the y-coordinate of the lower-right corner of the display
	)

	Note that the (0, 0) origin is the top-left corner of the main display (not
	necessarily Display 1).  If you have parts of any monitor to the left or
	above the top-left corner of the main display, you will see some negative x/y
	coordinates.

	Internally, this grabs the geometry from Windows at least twice to avoid
	getting bad geometry during changes to the display configuration.

	Raises L{RectFailed} if the geometry cannot be retrieved, though
	this failure mode has never been observed.
	"""
	HANDLE_MONITOR, HDC_MONITOR, SCREEN_RECT = range(3)

	# My experiments show this needs to be no more than 3 (for 4 iterations
	# through the loop), but use 150 in case there are pathological systems.
	# Note that one iteration of the loop takes about 90us on a Q6600.
	tries = 150
	lastRects = None
	for _ in range(tries):
		try:
			monitors = win32api.EnumDisplayMonitors(None, None)
		except SystemError:
			# If you are changing your monitor configuration while EnumDisplayMonitors
			# is enumerating the displays, it may throw SystemError.  We just try
			# again in this case.
			lastRects = None
		else:
			for m in monitors:
				m[HDC_MONITOR].Close()
			rects = list(m[SCREEN_RECT] for m in monitors)
			try:
				for rect in rects:
					checkRect(rect)
			except ValueError:
				lastRects = None
			else:
				if rects == lastRects:
					return rects
				else:
					lastRects = rects

	raise RectFailed("Could not get stable rect information after %d tries; "
		"last was %r." % (tries, lastRects))


class GrabFailed(Exception):
	"""
	Could not take a screenshot.
	"""



def deleteDCAndBitMap(dc, bitmap):
	dc.DeleteDC()
	handle = bitmap.GetHandle()
	# Trying to DeleteObject(0) will throw an exception; it can be 0 in the case
	# of an untouched win32ui.CreateBitmap()
	if handle != 0:
		win32gui.DeleteObject(handle)

# In case someone rightfully imported the private helper before we made it public
_deleteDCAndBitMap = deleteDCAndBitMap


def getDCAndBitMap(saveBmpFilename=None, rect=None):
	"""
	Returns a (DC, PyCBitmap).  On the returned DC ("device context"), you
	*must* call aDC.DeleteDC().  On the returned PyCBitmap, you *must* call
	win32gui.DeleteObject(aPyCBitmap.GetHandle()).

	If C{saveBmpFilename} is provided, a .bmp will be saved to the specified
	filename.  This does not require PIL.  The .bmp file will have the same
	bit-depth as the screen; it is not guaranteed to be 32-bit.  If you provide
	this argument, you still must clean up the returned objects, as mentioned.

	If C{rect} is not C{None}, instead of capturing the entire virtual screen,
	only the region inside the rect will be captured.  C{rect} is a tuple of (
		the x-coordinate of the upper-left corner of the virtual screen,
		the y-coordinate of the upper-left corner of the virtual screen,
		the x-coordinate of the lower-right corner of the virtual screen,
		the y-coordinate of the lower-right corner of the virtual screen
	)

	Note that both x and y coordinates may be negative; the (0, 0) origin is
	determined by the top-left corner of the main display (not necessarily
	Display 1).

	Raises L{GrabFailed} if unable to take a screenshot (e.g. due to locked
	workstation, no display, or active UAC elevation screen).

	Raises L{ValueError} if C{rect}'s computed width or height is zero or
	negative, or if rect contains nonsense.
	"""
	if rect is None:
		try:
			rect = getVirtualScreenRect()
		except RectFailed as e:
			raise GrabFailed("Error during getVirtualScreenRect: " + str(e))
		# rect is already checked
	else:
		checkRect(rect)

	left, top, right, bottom = rect
	width = right - left
	height = bottom - top

	hwndDesktop = win32gui.GetDesktopWindow()

	# Retrieve the device context (DC) for the entire virtual screen.
	hwndDevice = win32gui.GetWindowDC(hwndDesktop)
	##print("device", hwndDevice)
	assert isinstance(hwndDevice, (int, long)), hwndDevice

	mfcDC  = win32ui.CreateDCFromHandle(hwndDevice)
	try:
		saveDC = mfcDC.CreateCompatibleDC()
		saveBitMap = win32ui.CreateBitmap()
		# Above line is assumed to never raise an exception.
		try:
			try:
				saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
			except (win32ui.error, OverflowError) as e:
				raise GrabFailed("Could not CreateCompatibleBitmap("
					"mfcDC, %r, %r) - perhaps too big? Error was: %s" % (width, height, e))
			saveDC.SelectObject(saveBitMap)
			try:
				saveDC.BitBlt((0, 0), (width, height), mfcDC, (left, top), win32con.SRCCOPY)
			except win32ui.error as e:
				raise GrabFailed("Error during BitBlt. "
					"Possible reasons: locked workstation, no display, "
					"or an active UAC elevation screen. Error was: " + str(e))
			if saveBmpFilename is not None:
				saveBitMap.SaveBitmapFile(saveDC, saveBmpFilename)
		except:
			deleteDCAndBitMap(saveDC, saveBitMap)
			# Let's just hope the above line doesn't raise an exception
			# (or it will mask the previous exception)
			raise
	finally:
		mfcDC.DeleteDC()

	return saveDC, saveBitMap


class BITMAPINFOHEADER(ctypes.Structure):
	_fields_ = [
		('biSize', ctypes.c_uint32),
		('biWidth', ctypes.c_int),
		('biHeight', ctypes.c_int),
		('biPlanes', ctypes.c_short),
		('biBitCount', ctypes.c_short),
		('biCompression', ctypes.c_uint32),
		('biSizeImage', ctypes.c_uint32),
		('biXPelsPerMeter', ctypes.c_long),
		('biYPelsPerMeter', ctypes.c_long),
		('biClrUsed', ctypes.c_uint32),
		('biClrImportant', ctypes.c_uint32)
	]



class BITMAPINFO(ctypes.Structure):
	_fields_ = [
		('bmiHeader', BITMAPINFOHEADER),
		('bmiColors', ctypes.c_ulong * 3)
	]



class DIBFailed(Exception):
	pass



def getBGR32(dc, bitmap):
	"""
	Returns a (raw BGR str, (width, height)) for C{dc}, C{bitmap}.
	Guaranteed to be 32-bit.  Note that the origin of the returned image is
	in the bottom-left corner, and the image has 32-bit line padding.
	"""
	bmpInfo = bitmap.GetInfo()
	width, height = bmpInfo['bmWidth'], bmpInfo['bmHeight']

	bmi = BITMAPINFO()
	ctypes.memset(ctypes.byref(bmi), 0x00, ctypes.sizeof(bmi))
	bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
	bmi.bmiHeader.biWidth = width
	bmi.bmiHeader.biHeight = height
	bmi.bmiHeader.biBitCount = 24
	bmi.bmiHeader.biPlanes = 1

	bufferLen = height * ((width * 3 + 3) & -4)
	pbBits = ctypes.create_string_buffer(bufferLen)

	ret = ctypes.windll.gdi32.GetDIBits(
		dc.GetHandleAttrib(),
		bitmap.GetHandle(),
		0,
		height,
		ctypes.byref(pbBits),
		ctypes.pointer(bmi),
		win32con.DIB_RGB_COLORS)
	if ret == 0:
		raise DIBFailed("Return code 0 from GetDIBits")

	assert len(pbBits.raw) == bufferLen, len(pbBits.raw)

	return pbBits.raw, (width, height)


def _getRectAsImage(rect):
	try:
		# Pillow or PIL
		from PIL import Image
	except ImportError:
		# some old PIL installations
		import Image

	dc, bitmap = getDCAndBitMap(rect=rect)
	try:
		bmpInfo = bitmap.GetInfo()
		# bmpInfo is something like {
		# 	'bmType': 0, 'bmWidthBytes': 5120, 'bmHeight': 1024,
		# 	'bmBitsPixel': 32, 'bmPlanes': 1, 'bmWidth': 1280}
		##print(bmpInfo)
		size = (bmpInfo['bmWidth'], bmpInfo['bmHeight'])

		if bmpInfo['bmBitsPixel'] == 32:
			# Use GetBitmapBits and BGRX if the bpp == 32, because
			# it's ~15% faster than the method below.
			data = bitmap.GetBitmapBits(True) # asString=True
			return Image.frombuffer(
				'RGB', size, data, 'raw', 'BGRX', 0, 1)
		else:
			# If bpp != 32, we cannot use GetBitmapBits, because it
			# does not return a 24/32-bit image when the screen is at
			# a lower color depth.
			try:
				data, size = getBGR32(dc, bitmap)
			except DIBFailed as e:
				raise GrabFailed("getBGR32 failed. Error was " + str(e))
			# BGR, 32-bit line padding, origo in lower left corner
			return Image.frombuffer(
				'RGB', size, data, 'raw', 'BGR', (size[0] * 3 + 3) & -4, -1)
	finally:
		deleteDCAndBitMap(dc, bitmap)


def getScreenAsImage():
	"""
	Returns a PIL Image object (mode RGB) of the entire virtual screen.

	Raises L{GrabFailed} if unable to take a screenshot (e.g. due to locked
	workstation, no display, or active UAC elevation screen).
	"""
	return _getRectAsImage(None)


def normalizeRects(rects):
	"""
	Normalize a list of rects (e.g. as returned by L{getDisplayRects()})
	to make all coordinates >= 0.  This is useful if you want to do your own
	cropping of an entire virtual screen as returned by L{getScreenAsImage()}.
	"""
	smallestX = min(rect[0] for rect in rects)
	smallestY = min(rect[1] for rect in rects)
	return list(
		(-smallestX + left,
		 -smallestY + top,
		 -smallestX + right,
		 -smallestY + bottom) for left, top, right, bottom in rects
	)


def getDisplaysAsImages():
	"""
	Returns a list of PIL Image objects (mode RGB), one for each display.
	This list is ordered by display number.

	Internally, this captures the entire virtual screen and then crops out each
	Image based on display information.  This method ensures that all displays
	are captured at the same time (or as close to it as Windows permits).

	Raises L{GrabFailed} if unable to take a screenshot (e.g. due to locked
	workstation, no display, or active UAC elevation screen).
	"""
	try:
		rects = getDisplayRects()
	except RectFailed as e:
		raise GrabFailed("Error during getDisplayRects: " + str(e))
	# im has an origin at (0, 0) in the top-left corner of the virtual screen,
	# but our `rect`s have a (0, 0) origin in the top-left corner of the main
	# display.  So we normalize all coordinates in the rects to be >= 0.
	normalizedRects = normalizeRects(rects)
	im = getScreenAsImage()

	return list(im.crop(rect) for rect in normalizedRects)


def getRectAsImage(rect):
	"""
	Returns a PIL Image object (mode RGB) of the region inside the rect.

	See the L{getDCAndBitMap} docstring for C{rect} documentation.

	Raises L{GrabFailed} if unable to take a screenshot (e.g. due to locked
	workstation, no display, or active UAC elevation screen).

	Raises L{ValueError} if C{rect}'s computed width or height is zero or
	negative, or if rect contains nonsense.

	Raises L{TypeError} if C{rect} is C{None}.
	"""
	if rect is None:
		raise TypeError("Expected a tuple for rect, got None")
	return _getRectAsImage(rect)


def saveScreenToBmp(bmpFilename):
	"""
	Save a screenshot of the entire virtual screen to a .bmp file.  Does not
	require PIL.  The .bmp file will have the same bit-depth as the screen;
	it is not guaranteed to be 32-bit.

	Raises L{GrabFailed} if unable to take a screenshot (e.g. due to locked
	workstation, no display, or active UAC elevation screen).
	"""
	dc, bitmap = getDCAndBitMap(bmpFilename)
	deleteDCAndBitMap(dc, bitmap)


def saveRectToBmp(bmpFilename, rect):
	"""
	Save a screenshot of the region inside the rect to a .bmp file.  Does not
	require PIL.  The .bmp file will have the same bit-depth as the screen;
	it is not guaranteed to be 32-bit.

	See the L{getDCAndBitMap} docstring for C{rect} documentation.

	Raises L{GrabFailed} if unable to take a screenshot (e.g. due to locked
	workstation, no display, or active UAC elevation screen).

	Raises L{ValueError} if C{rect}'s computed width or height is zero or
	negative, or if rect contains nonsense.

	Raises L{TypeError} if C{rect} is C{None}.
	"""
	if rect is None:
		raise TypeError("Expected a tuple for rect, got None")
	dc, bitmap = getDCAndBitMap(bmpFilename, rect)
	deleteDCAndBitMap(dc, bitmap)


def _demo():
	# Save the entire virtual screen as a BMP (no PIL required)
	saveScreenToBmp('screencapture_entire.bmp')

	# Save an arbitrary rectangle of the virtual screen as a BMP (no PIL required)
	saveRectToBmp('screencapture_256_256.bmp', rect=(0, 0, 256, 256))

	# Save the entire virtual screen as a PNG
	entireScreen = getScreenAsImage()
	entireScreen.save('screencapture_entire.png', format='png')

	# Get bounding rectangles for all displays, in display order
	print("Display rects are:", getDisplayRects())
	# -> something like [(0, 0, 1280, 1024), (-1280, 0, 0, 1024), (1280, -176, 3200, 1024)]

	# Capture an arbitrary rectangle of the virtual screen: (left, top, right, bottom)
	rect256 = getRectAsImage((0, 0, 256, 256))
	rect256.save('screencapture_256_256.png', format='png')

	# Unsynchronized capture, one display at a time.
	# If you need all displays, use getDisplaysAsImages() instead.
	for displayNumber, rect in enumerate(getDisplayRects(), 1):
		imDisplay = getRectAsImage(rect)
		imDisplay.save('screencapture_unsync_display_%d.png' % (displayNumber,), format='png')

	# Synchronized capture, entire virtual screen at once, cropped to one Image per display.
	for displayNumber, im in enumerate(getDisplaysAsImages(), 1):
		im.save('screencapture_sync_display_%d.png' % (displayNumber,), format='png')


if __name__ == '__main__':
	_demo()
