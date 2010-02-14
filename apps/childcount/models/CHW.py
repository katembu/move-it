#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

'''ChildCount Models

CHW - Community Health Worker model
'''

import re

from django.db import models
from django.utils.translation import ugettext_lazy as _

from reporters.models import Reporter
from locations.models import Location

from childcount.models import Clinic


class CHW(Reporter):

    '''Community Health Worker model'''

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Community Health Worker")
        verbose_name_plural = _(u"Community Health Workers")

    '''
    zones = models.ManyToManyField(Location, verbose_name=_(u"Locations"), \
                                   related_name='responsible_chw',
                                   help_text=_(u"The locations this CHW " \
                                                "covers"))
    '''

    clinic = models.ForeignKey(Clinic, verbose_name=_(u"Clinic"), \
                               blank=True, null=True,
                               related_name='stationed_chw', \
                               help_text=_(u"The clinic this CHW reports to"))
