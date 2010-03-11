# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
from zope.interface import implements
from zope.component.interfaces import ObjectEvent
from affinitic.zamqp.interfaces import IArrivedMessage


class ArrivedMessage(ObjectEvent):
    implements(IArrivedMessage)

    def __init__(self, object):
        self.object = object
        self.data = object.payload
