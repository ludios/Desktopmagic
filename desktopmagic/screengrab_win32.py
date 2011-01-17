"""
Robust functions for grabbing and saving screenshots on Windows.
"""

# TODO: support capture of individual displays (and at the same time with a "single screenshot")
# Use GetDeviceCaps; see http://msdn.microsoft.com/en-us/library/dd144877%28v=vs.85%29.aspx

import win32gui
import win32ui
import win32con
import win32api


class GrabFailed(Exception):
	"""
	Could not take a screenshot.
	"""



def _getScreenBitMap(saveBmpFilename=None):
	"""
	Returns a PyCBitmap.  On the returned object x, you *must* call
	win32gui.DeleteObject(x.GetHandle()) to free memory.
	"""
	hwndDesktop = win32gui.GetDesktopWindow()

	# Get complete virtual screen, including all monitors.
	left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
	top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
	width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
	height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
	##print "L", left, "T", top, "dim:", width, "x", height

	# Retrieve the device context (DC) for the entire window.
	hwndDevice = win32gui.GetWindowDC(hwndDesktop)
	##print "device", hwndDevice
	assert isinstance(hwndDevice, (int, long)), hwndDevice

	mfcDC  = win32ui.CreateDCFromHandle(hwndDevice)
	try:
		saveDC = mfcDC.CreateCompatibleDC()
		try:
			saveBitMap = win32ui.CreateBitmap()
			try:
				saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
				saveDC.SelectObject(saveBitMap)
				try:
					saveDC.BitBlt((0, 0), (width, height), mfcDC, (left, top), win32con.SRCCOPY)
				except win32ui.error, e:
					raise GrabFailed("Error during BitBlt.  "
						"Workstation might be locked.  Error was: " + str(e))
				if saveBmpFilename is not None:
					saveBitMap.SaveBitmapFile(saveDC, saveBmpFilename)
			except:
				win32gui.DeleteObject(saveBitMap.GetHandle())
				raise
		finally:
			saveDC.DeleteDC()
	finally:
		mfcDC.DeleteDC()

	return saveBitMap


def getScreenRawBytes():
	"""
	Returns a (raw BGRX str, (width, height)) of the current screen
	(incl. all monitors).
	"""
	saveBitMap = _getScreenBitMap()
	try:
		bmpInfo = saveBitMap.GetInfo()
		# bmpInfo is something like {
		# 	'bmType': 0, 'bmWidthBytes': 5120, 'bmHeight': 1024,
		# 	'bmBitsPixel': 32, 'bmPlanes': 1, 'bmWidth': 1280}
		##print bmpInfo

		width, height = bmpInfo['bmWidth'], bmpInfo['bmHeight']
		bgrxStr = saveBitMap.GetBitmapBits(True)
		return bgrxStr, (width, height)
	finally:
		win32gui.DeleteObject(saveBitMap.GetHandle())


def getScreenAsImage():
	"""
	Returns a PIL Image object of the current screen (incl. all monitors).
	"""
	import Image

	bgrxStr, dimensions = getScreenRawBytes()
	return Image.frombuffer('RGB', dimensions, bgrxStr, 'raw', 'BGRX', 0, 1)


def saveScreenToBmp(bmpFilename):
	"""
	Save a screenshot (incl. all monitors) to a .bmp file.  Does not require PIL.
	"""
	saveBitMap = _getScreenBitMap(saveBmpFilename=bmpFilename)
	win32gui.DeleteObject(saveBitMap.GetHandle())


def _demo():
	saveScreenToBmp('screencapture.bmp')
	im = getScreenAsImage()
	im.save('screencapture.png', format='png')


if __name__ == '__main__':
	_demo()
