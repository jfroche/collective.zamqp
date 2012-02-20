# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl
"""
import os
import glob

from unittest import TestSuite

from zope.testing import doctest

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
    return TestSuite([doctest.DocFileSuite(os.path.basename(filename),
                                           setUp=setUp,
                                           optionflags=OPTIONFLAGS,
                                           package='affinitic.zamqp.tests')
                      for filename in filenames])
