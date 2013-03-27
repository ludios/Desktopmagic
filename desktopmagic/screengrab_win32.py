"""
Robust functions for grabbing and saving screenshots on Windows.
"""

# TODO: check screen metrics and EnumDisplayMonitors at least twice (in a loop) to avoid
# race conditions during monitor changes

import ctypes
import win32gui
import win32ui
import win32con
import win32api


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

	Note that both x and y coordinates may be negative; the (0, 0) origin is determined
	by the top-left corner of Display 1.
	"""
	HANDLE_MONITOR, HDC_MONITOR, SCREEN_RECT = range(3)

	monitors = win32api.EnumDisplayMonitors(None, None)
	for m in monitors:
		m[HDC_MONITOR].Close()

	return list(m[SCREEN_RECT] for m in monitors)


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



class GrabFailed(Exception):
	"""
	Could not take a screenshot.
	"""



class DIBFailed(Exception):
	pass



def _deleteDCAndBitMap(dc, bitmap):
	dc.DeleteDC()
	handle = bitmap.GetHandle()
	# Trying to DeleteObject(0) will throw an exception; it can be 0 in the case
	# of an untouched win32ui.CreateBitmap()
	if handle != 0:
		win32gui.DeleteObject(handle)


def getDCAndBitMap(saveBmpFilename=None, rect=None):
	"""
	Returns a (DC, PyCBitmap).  On the returned PyCBitmap, you *must* call
	win32gui.DeleteObject(aPyCBitmap.GetHandle()).  On the returned DC
	("device context"), you *must* call aDC.DeleteDC()

	If C{saveBmpFilename} is provided, a .bmp will be saved to the specified
	location.  This does not require PIL.  The .bmp file will have the same bit-depth
	as the screen; it is not guaranteed to be 32-bit.  If you pass this argument, you
	still must call C{DeleteObject} and C{DeleteDC()} on the returned objects.

	If C{rect} is provided, instead of capturing the entire virtual screen, only the
	region inside the rect will be captured.  C{rect} is a tuple of (
		the x-coordinate of the upper-left corner of the virtual screen,
		the y-coordinate of the upper-left corner of the virtual screen,
		the x-coordinate of the lower-right corner of the virtual screen,
		the y-coordinate of the lower-right corner of the virtual screen
	)

	Note that both x and y coordinates may be negative; the (0, 0) origin is determined
	by the top-left corner of Display 1.
	"""
	if rect is None:
		# Get complete virtual screen, including all monitors.  Note that left/top may be negative.
		# http://msdn.microsoft.com/en-us/library/windows/desktop/ms724385%28v=vs.85%29.aspx
		left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
		top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
		width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
		height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
		##print "L", left, "T", top, "dim:", width, "x", height
	else:
		left, top, right, bottom = rect
		width = right - left
		height = bottom - top

	hwndDesktop = win32gui.GetDesktopWindow()

	# Retrieve the device context (DC) for the entire virtual screen.
	hwndDevice = win32gui.GetWindowDC(hwndDesktop)
	##print "device", hwndDevice
	assert isinstance(hwndDevice, (int, long)), hwndDevice

	mfcDC  = win32ui.CreateDCFromHandle(hwndDevice)
	try:
		saveDC = mfcDC.CreateCompatibleDC()
		saveBitMap = win32ui.CreateBitmap()
		# Above line is assumed to never raise an exception.
		try:
			saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
			saveDC.SelectObject(saveBitMap)
			try:
				saveDC.BitBlt((0, 0), (width, height), mfcDC, (left, top), win32con.SRCCOPY)
			except win32ui.error, e:
				raise GrabFailed("Error during BitBlt. "
					"Possible reasons: locked workstation, no display, "
					"or an active UAC elevation screen. Error was: " + str(e))
			if saveBmpFilename is not None:
				saveBitMap.SaveBitmapFile(saveDC, saveBmpFilename)
		except:
			_deleteDCAndBitMap(saveDC, saveBitMap)
			# Let's just hope the above line doesn't raise an exception
			# (or it will mask the previous exception)
			raise
	finally:
		mfcDC.DeleteDC()

	return saveDC, saveBitMap


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
	import Image

	dc, bitmap = getDCAndBitMap(rect=rect)
	try:
		bmpInfo = bitmap.GetInfo()
		# bmpInfo is something like {
		# 	'bmType': 0, 'bmWidthBytes': 5120, 'bmHeight': 1024,
		# 	'bmBitsPixel': 32, 'bmPlanes': 1, 'bmWidth': 1280}
		##print bmpInfo
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
			except DIBFailed, e:
				raise GrabFailed("getBGR32 failed. Error was " + str(e))
			# BGR, 32-bit line padding, origo in lower left corner
			return Image.frombuffer(
				'RGB', size, data, 'raw', 'BGR', (size[0] * 3 + 3) & -4, -1)
	finally:
		_deleteDCAndBitMap(dc, bitmap)


def getScreenAsImage():
	"""
	Returns a PIL Image object (mode RGB) of the entire virtual screen.
	"""
	return _getRectAsImage(None)


def _normalizeRects(rects):
	smallestX = min(rect[0] for rect in rects)
	smallestY = min(rect[1] for rect in rects)
	normalizedRects = []
	for left, top, right, bottom in rects:
		normalizedRects.append(
			(-smallestX + left,
			 -smallestY + top,
			 -smallestX + right,
			 -smallestY + bottom))
	return normalizedRects


def getDisplaysAsImages():
	"""
	Returns a list of PIL Image objects (mode RGB), one for each display.
	This list is ordered by display number.

	Internally, this captures the entire virtual screen and then crops out each
	Image based on display information.  This method ensures all displays
	are captured at the same time (or as close to it as Windows permits).
	"""
	import Image

	# im has an origin at (0, 0), but the `rect` information in our rects may
	# have negative x and y coordinates.  So we normalize all the coordinates
	# in the rects to be >= 0.
	normalizedRects = _normalizeRects(getDisplayRects())
	im = getScreenAsImage()

	return list(im.crop(rect) for rect in normalizedRects)


def getRectAsImage(rect):
	"""
	Returns a PIL Image object (mode RGB) of the region inside the rect.
	See L{getDCAndBitMap} docstring for C{rect} documentation.

	Note that both x and y coordinates may be negative; the (0, 0) origin is determined
	by the top-left corner of Display 1.
	"""
	return _getRectAsImage(rect)


def saveScreenToBmp(bmpFilename):
	"""
	Save a screenshot of the entire virtual screen to a .bmp file.  Does not
	require PIL.  The .bmp file will have the same bit-depth as the screen;
	it is not guaranteed to be 32-bit.
	"""
	dc, bitmap = getDCAndBitMap(saveBmpFilename=bmpFilename, rect=None)
	_deleteDCAndBitMap(dc, bitmap)


def saveRectToBmp(bmpFilename, rect):
	"""
	Save a screenshot of the region inside the rect to a .bmp file.  Does not
	require PIL.  The .bmp file will have the same bit-depth as the screen;
	it is not guaranteed to be 32-bit.

	See L{getDCAndBitMap} docstring for C{rect} documentation.
	"""
	dc, bitmap = getDCAndBitMap(saveBmpFilename=bmpFilename, rect=rect)
	_deleteDCAndBitMap(dc, bitmap)


def _demo():
	# Save the entire virtual screen as a BMP (no PIL required)
	saveScreenToBmp('screencapture_entire.bmp')

	# Save an arbitrary rectangle of the virtual screen as a BMP (no PIL required)
	saveRectToBmp('screencapture_256_256.bmp', rect=(0, 0, 256, 256))

	# Save the entire virtual screen as a PNG
	entireScreen = getScreenAsImage()
	entireScreen.save('screencapture_entire.png', format='png')

	# Capture an arbitrary rectangle of the virtual screen: (left, top, right, bottom)
	rect256 = getRectAsImage((0, 0, 256, 256))
	rect256.save('screencapture_256_256.png', format='png')

	# Unsynchronized capture, one display at a time.
	# If you need all displays, use getDisplaysAsImages() instead.
	for displayNumber, rect in enumerate(getDisplayRects()):
		imDisplay = getRectAsImage(rect)
		imDisplay.save('screencapture_unsync_display_%d.png' % (displayNumber,), format='png')

	# Synchronized capture, entire virtual screen at once, but with one Image per display.
	for displayNumber, im in enumerate(getDisplaysAsImages()):
		im.save('screencapture_sync_display_%d.png' % (displayNumber,), format='png')


if __name__ == '__main__':
	_demo()
