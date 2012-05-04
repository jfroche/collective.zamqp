AMQP integration for Zope2
==========================

This package is an almost complete rewrite of
`affinitic.zamqp <http://pypi.python.org/pypi/affinitic.zamqp>`_,
but preserves its ideas on configuring producers and consumers.

**collective.zamqp** acts as a *Zope Server* by co-opting Zope's asyncore
mainloop (with asyncore-supporting AMQP-library
`pika <http://pypi.python.org/pypi/pika>`_ [0.9.5]),
and injecting consumed messages as *request* for Zope's ZPublisher
(similarly to Zope ClockServer).

TODO:
- rewrite documentation to reflect the new design
- update affinitic.zamqp's tests for the new design
