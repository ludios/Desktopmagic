Desktopmagic overview
=====================
Desktopmagic can take screenshots (Windows-only for now) without
leaking memory in any type of error case (locked workstation, no
monitor attached, etc).

You may want this instead of PIL's ImageGrab because:

*	Desktopmagic can take a screenshot of all monitors.  You can:

	*	Take a screenshot of the entire virtual screen.

	*	Take a screenshot of the entire virtual screen, split into separate PIL Images.

	*	Take a screenshot of just one display.

	*	Take a screenshot of an arbitrary region of the virtual screen.

	(See below)

*	PIL leaks memory if you try to take a screenshot when the
	workstation is locked (as of 2011-01).



Requirements
============
*	pywin32: http://sourceforge.net/projects/pywin32/files/pywin32/

*	PIL: http://www.pythonware.com/products/pil/ - unless you don't need
	`getScreenAsImage`, `getDisplaysAsImages`, or `getRectAsImage`.



Installation
============
`python setup.py install`

This installs the module `desktopmagic` and the script `screengrab_torture_test`.



Sample uses
==========
```
from desktopmagic.screengrab_win32 import (
	getDisplayRects, saveScreenToBmp, saveRectToBmp, getScreenAsImage,
	getRectAsImage, getDisplaysAsImages)

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
```

For more information, see the docstrings in https://github.com/ludios/Desktopmagic/blob/master/desktopmagic/screengrab_win32.py



Wishlist
========
*	OS X support

*	Linux support



Contributing
============
Patches and pull requests are welcome.

This coding standard applies: http://ludios.org/coding-standard/
