# -*- coding: utf-8 -*-
"""
affinitic.zamqp

Licensed under the GPL license, see LICENCE.txt for more details.

Copyright by Affinitic sprl
Copyright by University of Jyväskylä
"""
import threading

from App.config import getConfiguration
from affinitic.zamqp.processor import MultiProcessor

import logging
logger = logging.getLogger('affinitic.zamqp')


def start(event):
    """Start the queue processing services based on the settings in
    zope.conf on 'IDatabaseOpenedWithRoot' event"""

    # Read product configuration
    config = getattr(getConfiguration(), 'product_config', {})
    product_config = config.get('affinitic.zamqp', {})

    # Start configured services
    for service_id, opts in product_config.items():
        site_id, connection_id = opts.split('@')
        connection_id = connection_id.split(' ')[0]  # clean deprecated opts.

        # Start the thread running the processor inside
        processor = MultiProcessor(event.database, site_id, connection_id)

        thread = threading.Thread(target=processor, name=service_id)
        thread.setDaemon(True)
        thread.running = True
        thread.start()

        logger.info('Starting consumer %s', service_id)
