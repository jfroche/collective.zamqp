# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id$
"""
from time import sleep
import threading
from App.config import getConfiguration
from affinitic.zamqp.processor import MultiProcessor
import logging
logger = logging.getLogger('affinitic.zamqp')


def getAutostartServiceNames():
    """get a list of services to start"""
    config = getConfiguration().product_config
    if config is not None:
        task_config = config.get('affinitic.zamqp', None)
        if task_config:
            return task_config
    return {}


class ConsumerService(object):

    def startProcessing(self, serviceId, db, siteName, connectionId):
        """See interfaces.ITaskService"""
        # Start the thread running the processor inside.
        processor = MultiProcessor(db, siteName, connectionId)
        thread = threading.Thread(target=processor, name=serviceId)
        thread.setDaemon(True)
        thread.running = True
        thread.start()
        sleep(1)


def bootStrapSubscriber(event):
    """Start the queue processing services based on the
       settings in zope.conf"""
    serviceItems = getAutostartServiceNames()
    db = event.database
    for serviceId, serviceName in serviceItems.items():
        siteName, serviceName = serviceName.split('@')
        consumer = ConsumerService()
        logger.info('Starting consumer %s' % serviceId)
        consumer.startProcessing(serviceId, db, siteName, serviceName)
