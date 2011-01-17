from __future__ import with_statement

import win32gui
import win32ui
import win32con
import win32api


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

	# Retrieve the device context (DC) for the entire window.
	hwndDevice = win32gui.GetWindowDC(hwndDesktop)
	assert isinstance(hwndDevice, (int, long)), hwndDevice

	mfcDC  = win32ui.CreateDCFromHandle(hwndDevice)
	try:
		saveDC = mfcDC.CreateCompatibleDC()
		try:
			saveBitMap = win32ui.CreateBitmap()
			try:
				saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
				saveDC.SelectObject(saveBitMap)
				saveDC.BitBlt((0, 0), (width, height), mfcDC, (left, top), win32con.SRCCOPY)
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
	Returns a (raw BGRX str, (width, height))
	"""
	try:
		saveBitMap = _getScreenBitMap()
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
	Returns a PIL Image object of the current screen.
	"""
	import Image

	bgrxStr, dimensions = getScreenRawBytes()
	return Image.frombuffer('RGB', dimensions, bgrxStr, 'raw', 'BGRX', 0, 1)


def saveScreenToBmp(bmpFilename):
	"""
	Save a screenshot to a .bmp file.  Does not require PIL.
	"""
	saveBitMap = _getScreenBitMap(saveBmpFilename=bmpFilename)
	win32gui.DeleteObject(saveBitMap.GetHandle())


def _demo():
	im = getScreenAsImage()
	im.save('screencapture.png', format='png')
	saveScreenToBmp('screencapture.bmp')


if __name__ == '__main__':
	_demo()
