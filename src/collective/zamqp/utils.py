# -*- coding: utf-8 -*-
"""Helpers for re-using amqp-supporting packages between different buildouts"""

from App.config import getConfiguration


def getBuildoutName():
    cfg = getConfiguration()
    # under a buildout environment cfg.instancehome is usually something like
    # '/var/buildouts/buildout_name/parts/instance'
    parts = getattr(cfg, 'instancehome', '').split('/')
    if len(parts) > 2:
        return parts[-3]
    else:
        # configuration not found, return some sane default string
        return 'collective.zamqp.default'
