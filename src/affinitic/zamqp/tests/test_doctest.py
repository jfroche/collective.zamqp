# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
import os
import glob
from zope.testing import doctest
from Globals import package_home
from unittest import TestSuite
from affinitic.zamqp.tests import GLOBALS

OPTIONFLAGS = (doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE |
               doctest.REPORT_ONLY_FIRST_FAILURE)


def list_doctests():
    home = package_home(GLOBALS)
    return [filename for filename in
            glob.glob(os.path.sep.join([home, '*.txt']))]


def test_suite():
    filenames = list_doctests()
    suite = TestSuite()
    suites = [suite.addtest(os.path.basename(filename),
               optionflags=OPTIONFLAGS,
               package='affinitic.zamqp')
              for filename in filenames]
    return suites
