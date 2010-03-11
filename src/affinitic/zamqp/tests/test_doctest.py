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
from unittest import TestSuite
import zope.configuration.xmlconfig

OPTIONFLAGS = (doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE |
               doctest.REPORT_ONLY_FIRST_FAILURE)
testPath = os.path.normpath(os.path.dirname(__file__))


def list_doctests():
    return [filename for filename in
            glob.glob(os.path.sep.join([testPath, '*.txt']))]


def setUp(suite):
    import affinitic.zamqp
    zope.configuration.xmlconfig.XMLConfig('testing.zcml', affinitic.zamqp)()


def test_suite():
    filenames = list_doctests()
    return TestSuite([doctest.DocFileSuite(
                            os.path.basename(filename),
               setUp=setUp,
               optionflags=OPTIONFLAGS,
               package='affinitic.zamqp.tests')
              for filename in filenames])
