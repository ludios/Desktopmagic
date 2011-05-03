#!/usr/bin/env python

from distutils.core import setup

import desktopmagic

setup(
	name='Desktopmagic',
	version=desktopmagic.__version__,
	description="Robust multi-monitor screenshot grabber (Windows-only right now)",
	url="https://github.com/ludios/Desktopmagic",
	author="Ivan Kozik",
	author_email="ivan@ludios.org",
	classifiers=[
		'Programming Language :: Python :: 2',
		'Development Status :: 4 - Beta',
		'Environment :: Win32 (MS Windows)',
		'Operating System :: Microsoft :: Windows',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: MIT License',
	],
	packages=['desktopmagic', 'desktopmagic.scripts', 'desktopmagic.test'],
	scripts=['bin/screengrab_torture_test'],
)
