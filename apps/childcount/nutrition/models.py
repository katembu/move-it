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
        
    OEDEMA_YES = 'Y'
    OEDEMA_NO = 'N'
    OEDEMA_UNKOWN = 'U'
    OEDEMA_CHOICES = (
        (OEDEMA_YES, _(u"Yes")),
        (OEDEMA_NO, _(u"No")),
        (OEDEMA_UNKOWN, _(u"Unknown")))

    muac = models.SmallIntegerField(_(u"MUAC (mm)"))
    oedema = models.CharField(_(u"Oedema"), max_length=1, \
                              choices=OEDEMA_CHOICES)
    status = models.IntegerField(choices=STATUS_CHOICES, db_index=True, \
                                 blank=True, null=True)

    def diagnose(self):
        '''Diagnosis of the patient'''
        self.status = self.STATUS_HEALTHY
        if self.oedema == 'Y' or self.muac < 110:
            self.status = self.STATUS_SEVERE
        elif self.muac < 125:
            self.status = self.STATUS_MODERATE
