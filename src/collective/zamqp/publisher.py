# -*- coding: utf-8 -*-
###
# collective.zamqp
#
# Licensed under the GPL license, see LICENCE.txt for more details.
#
# Copyright by Affinitic sprl
# Copyright (c) 2012 University of Jyväskylä
###

# BBB for collective.zamqp

from zope.deprecation import deprecated, moved

from collective.zamqp.producer import Producer


Publisher = Producer
deprecated('Publisher',
           'Publisher is no more. Please, use Producer instead.')

moved('collective.zamqp.producer', 'version 1.0.0')
