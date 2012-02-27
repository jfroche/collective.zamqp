# -*- coding: utf-8 -*-
###
# affinitic.zamqp
#
# Licensed under the GPL license, see LICENCE.txt for more details.
#
# Copyright by Affinitic sprl
# Copyright (c) 2012 University of Jyväskylä
###

# BBB for affinitic.zamqp

from zope.deprecation import deprecated, moved

from affinitic.zamqp.producer import Producer


Publisher = Producer
deprecated('Publisher',
           'Publisher is no more. Please, use Producer instead.')

moved('affinitic.zamqp.producer', 'version 3.0.0')
