AMQP integration for Zope2
==========================

This package is an almost complete rewrite of
`affinitic.zamqp <http://pypi.python.org/pypi/affinitic.zamqp>`_,
but preserves its ideas on how to setup AMQP-services
by configuring only producers and consumers.

**collective.zamqp** acts as a *Zope Server* by co-opting Zope's asyncore
mainloop (using asyncore-supporting AMQP-library
`pika <http://pypi.python.org/pypi/pika>`_),
and injecting consumed messages as *request* for Zope's ZPublisher
(exactly like Zope ClockServer does).

Therefore AMQP-messages are handled (by default) in a similar environment to
regular HTTP-request: ZCA-hooks, events and everything else behaving normally.

TODO:

* rewrite documentation to reflect the new design
* update affinitic.zamqp's tests for the new design

While we are still documenting and testing this, you may take a look at
`collective.zamqpdemo <http://github.com/datakurre/collective.zamqpdemo/>`_
for an example of use.
