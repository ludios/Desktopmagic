Desktopmagic overview
=====================
Desktopmagic can take screenshots (Windows-only for now) without
leaking memory in any type of error case (locked workstation, no
monitor attached, etc).

You may want this instead of PIL's ImageGrab because:

*	This takes a screenshot of all monitors.

*	PIL leaks memory if you try to take a screenshot when the
	workstation is locked (as of 2011-01).


Installation
============
`python setup.py install`

This installs the module `desktopmagic`.


Sample use
==========
`desktopmagic.screengrab_win32.getScreenAsImage()` returns a PIL `Image` object
(mode RGB) of the current screen (all monitors).

You can save it to disk:

```
from desktopmagic.screengrab_win32 import getScreenAsImage

im = getScreenAsImage()
im.save('screencapture.png', format='png')
```

`desktopmagic.screengrab_win32.saveScreenToBmp(bmpFilename)` save a screenshot
(all monitors) to a .bmp file.  This does not require PIL.  The .bmp file will
have the same bit-depth as the screen; it is not guaranteed to be 32-bit.
You'll get an probably-unreadable BMP if your screen depth is 256 colors.

See the source for more advanced/raw usage.


Wishlist
========
*	Support taking screenshots of just one monitor.

*	Support OS X

*	Support Linux

*	Write some tests
