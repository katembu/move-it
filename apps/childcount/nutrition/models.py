#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Malnutrition App Models

ReportMalnutrition - record malnutrition measurements
'''

from django.db import models
from django.utils.translation import ugettext as _

from childcount.core.models.Reports import PatientReport

class MUACReport(PatientReport):

    '''record malnutrition measurements'''
    
    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"MUAC Report")
        verbose_name_plural = _(u"MUAC Reports")

    STATUS_MODERATE = 1
    STATUS_SEVERE = 2
    STATUS_SEVERE_COMP = 3
    STATUS_HEALTHY = 4

    STATUS_CHOICES = (
        (STATUS_MODERATE, _(u"MAM")),
        (STATUS_SEVERE, _(u"SAM")),
        (STATUS_SEVERE_COMP, _(u"SAM+")),
        (STATUS_HEALTHY, _(u"Healthy")))

    muac = models.SmallIntegerField(_(u"MUAC (mm)"))
