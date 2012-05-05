collective.zamqp
================

*AMQP consumer and producer integration for Zope2*

.. uml::

   [Site] as Site1
   [Site] as Site2
   [Service] as Service1
   [Broker] as Broker

   Site1 .right.> Broker
   Broker .left.> Site1

   Site2 .down.> Broker
   Broker .up.> Site2

   Broker .right.> Service1
   Service1 .left.> Broker

Contents:

.. toctree::
   :maxdepth: 3

   introduction

While we are still documenting and testing this, you may take a look at
`collective.zamqpdemo <http://github.com/datakurre/collective.zamqpdemo/>`_
for an example of use.

.. Indices and tables
.. ==================
..
.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`

