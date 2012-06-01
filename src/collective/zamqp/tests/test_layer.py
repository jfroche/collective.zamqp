# -*- coding: utf-8 -*-
import unittest2 as unittest

from collective.zamqp.testing import (
    RABBIT_APP_FUNCTIONAL_TESTING,
    ZAMQP_FUNCTIONAL_TESTING,
    )


class RabbitFunctional(unittest.TestCase):

    layer = RABBIT_APP_FUNCTIONAL_TESTING

    def testNoQueues(self):
        rabbitctl = self.layer['rabbitctl']
        self.assertEqual('\n'.join(rabbitctl('list_queues')),
                         'Listing queues ...\n...done.\n\n')


class ZAMQPFunctional(unittest.TestCase):

    layer = ZAMQP_FUNCTIONAL_TESTING

    def testNoQueues(self):
        from collective.zamqp import connection
        connection.connect_all()

        from zope.testing.loggingsupport import InstalledHandler
        handler = InstalledHandler("collective.zamqp")

        import asyncore
        asyncore.loop(timeout=1, count=10)
        for record in handler.records: print record.getMessage()

        rabbitctl = self.layer['rabbitctl']
        self.assertIn("my.queue\t0", rabbitctl('list_queues')[0].split("\n"))
