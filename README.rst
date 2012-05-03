AMQP integration for Zope2
==========================

This is an almost complete rewrite of `affinitic.zamqp`_, but preserves
*affinitic.zamqp*'s ideas on configuring producers and consumers.
*collective.zamqp* acts as a "Zope Server" by co-opting Zope's asyncore
mainloop (with asyncore-supporting AMQP-library pika_ 0.9.5), and injecting
consumed messages as "request" for Zope's ZPublisher (similarly to Zope
ClockServer).

.. _affinitic.zamqp: http://pypi.python.org/pypi/affinitic.zamqp
.. _pika: http://pypi.python.org/pypi/pika

TODO:
- rewrite documentation to reflect the new design
- update affinitic.zamqp's tests for the new design
