#!/usr/bin/env python

from distutils.core import setup

import desktopmagic

setup(
	name='desktopmagic',
	version=desktopmagic.__version__,
	description="Python utilities useful in a desktop environment.",
	packages=['desktopmagic', 'desktopmagic.scripts', 'desktopmagic.test'],
	scripts=['bin/screengrab_torture_test'],
)
