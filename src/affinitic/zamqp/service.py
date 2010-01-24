# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.
Copyright by Affinitic sprl

$Id: event.py 67630 2006-04-27 00:54:03Z jfroche $
"""
import logging
import threading
import time

from zope.app.publication.zopepublication import ZopePublication
from App.config import getConfiguration
from ZPublisher.HTTPRequest import HTTPRequest
from ZPublisher.HTTPResponse import HTTPResponse
import ZPublisher

log = logging.getLogger('affinitic.zamqp')

ERROR_MARKER = object()
storage = threading.local()


def getAutostartServiceNames():
    """get a list of services to start"""

    config = getConfiguration().product_config
    if config is not None:
        task_config = config.get('affinitic.zamqp', None)
        if task_config:
            autostart = task_config.get('autostart', '')
            serviceNames = [name.strip()
                            for name in autostart.split(',')]
    return serviceNames


class ConsumerProcessor(object):

    def __init__(self, db, servicePath, waitTime=3.0):
        self.db = db
        self.servicePath = servicePath
        self.waitTime = waitTime

    def processNext(self):
        self.call('acl_users2')

    def call(self, method, args=(), errorValue=ERROR_MARKER):
        path = [method] + self.servicePath[:]
        path.reverse()
        response = HTTPResponse()
        env = {'SERVER_NAME': 'dummy',
               'SERVER_PORT': '8080',
               'PATH_INFO': '/' + '/'.join(path)}
        request = HTTPRequest(None, env, response)
        conn = self.db.open()
        root = conn.root()
        request['PARENTS'] = [root[ZopePublication.root_name]]
        try:
            try:
                ZPublisher.Publish.publish(request, 'Zope2', [None])
            except Exception, error:
                # This thread should never crash, thus a blank except
                log.error('Processor: ``%s()`` caused an error!' % method)
                log.exception(error)
                return errorValue is ERROR_MARKER and error or errorValue
        finally:
            request.close()
            conn.close()
            if not request.response.body:
                time.sleep(1)
            else:
                return request.response.body

    def __call__(self):
        while 1:
            result = self.processNext()
            print result
            # If there are no jobs available, sleep a little bit and then
            # check again.
            if not result:
                print 'nothing, we sleep'
                time.sleep(self.waitTime)


class ConsumerService(object):

    def startProcessing(self, app):
        """See interfaces.ITaskService"""
        # Start the thread running the processor inside.
        processor = ConsumerProcessor(app, [])
        thread = threading.Thread(target=processor, name='foo')
        thread.setDaemon(True)
        thread.running = True
        thread.start()


def bootStrapSubscriber(event):
    """Start the queue processing services based on the
       settings in zope.conf"""

    serviceNames = getAutostartServiceNames()

    db = event.database
    connection = db.open()
    root = connection.root()
    root_folder = root.get(ZopePublication.root_name, None)
    # we assume that portals can only added at site root level

    log.info('handling event IStartRemoteTasksEvent')

    for siteName, serviceName in [name.split('@')
                                  for name in serviceNames if name]:
        sites = [root_folder]
        print 'add consumer service %s' % serviceName
        #servicePath = [path for path in self.getPhysicalPath() if path]
        consumer = ConsumerService()
        consumer.startProcessing(db)
#        rootServices = list(rootSM.getUtilitiesFor(interfaces.ITaskService))
#
#        for site in sites:
#            csName = getattr(site, "__name__", '')
#            if csName is None:
#                csName = 'root'
#            if site is not None:
#                sm = site.getSiteManager()
#                if serviceName == '*':
#                    services = list(sm.getUtilitiesFor(interfaces.ITaskService))
#                    if siteName != "*" and siteName != '':
#                        services = [s for s in services
#                                       if s not in rootServices]
#                else:
#                    services = [(serviceName,
#                                 component.queryUtility(interfaces.ITaskService,
#                                                       context=site,
#                                                       name=serviceName))]
#                serviceCount = 0
#                for srvname, service in services:
#                    if service is not None and not service.isProcessing():
#                        service.startProcessing()
#                        serviceCount += 1
#                        msg = 'service %s on site %s started'
#                        log.info(msg % (srvname, csName))
#                    else:
#                        if siteName != "*" and serviceName != "*":
#                            msg = 'service %s on site %s not found'
#                            log.error(msg % (srvname, csName))
#            else:
#                log.error('site %s not found' % siteName)
#
#        if (siteName == "*" or serviceName == "*") and serviceCount == 0:
#            msg = 'no services started by directive %s'
#            log.warn(msg % name)
#
