# -*- coding: utf-8 -*-
from plone.testing import Layer, z2

from rabbitfixture.server import (
    RabbitServer,
    RabbitServerResources
    )


class FixedHostname(RabbitServerResources):
    """Allocate the resources a RabbitMQ server needs with the explicitly
    defined hostname.
    (Does not query the hostname from a socket as the default implementation
    does.)
    """

    @property
    def fq_nodename(self):
        """The node of the RabbitMQ that is being exported."""
        return "%s@%s" % (self.nodename, self.hostname)


class RabbitLayer(Layer):

    def setUp(self):
        # setup a RabbitMQ
        config = FixedHostname()
        self['rabbit'] = RabbitServer(config=config)
        self['rabbit'].setUp()
        # define a shortcut to rabbitmqctl
        self['rabbitctl'] = self['rabbit'].runner.environment.rabbitctl

    def tearDown(self):
        self['rabbit'].cleanUp()

RABBIT_FIXTURE = RabbitLayer()


class RabbitAppLayer(Layer):
    defaultBases = (RABBIT_FIXTURE, z2.STARTUP)

    def setUp(self):
        pass

    def tearDown(self):
        pass

RABBIT_APP_FIXTURE = RabbitAppLayer()


RABBIT_APP_INTEGRATION_TESTING = z2.IntegrationTesting(
    bases=(RABBIT_APP_FIXTURE,), name="RabbitAppFixture:Integration")
RABBIT_APP_FUNCTIONAL_TESTING = z2.FunctionalTesting(
    bases=(RABBIT_APP_FIXTURE,), name="RabbitAppFixture:Functional")
