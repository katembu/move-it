#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

'''ChildCount Models

CHWManager - Community Health Worker Manager model
'''

from django.db import models
from django.utils.translation import ugettext as _

from reporters.models import Reporter
from locations.models import Location
from childcount.models import Clinic


class CHWManager(Reporter):

    '''Community Health Worker Manager model'''

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"CHW Manager")
        verbose_name_plural = _(u"CHW Managers")

