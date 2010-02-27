# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl
"""
from time import sleep
from Products.Five import BrowserView


class ConsumerView(BrowserView):

    def __call__(self, message_data, message):
        print 'consume !'
        sleep(60)
        print 'after consume'
        message.ack()
        return True
