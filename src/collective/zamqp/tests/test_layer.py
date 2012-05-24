# -*- coding: utf-8 -*-
import unittest2 as unittest

from collective.zamqp.testing import RABBIT_APP_FUNCTIONAL_TESTING


class LayerTest(unittest.TestCase):

    layer = RABBIT_APP_FUNCTIONAL_TESTING

    def testNoQueues(self):
        rabbitctl = self.layer["rabbitctl"]
        self.assertEqual("\n".join(rabbitctl("list_queues")),
                         "Listing queues ...\n...done.\n\n")
