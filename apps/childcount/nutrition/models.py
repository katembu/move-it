#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Malnutrition App Models

ReportMalnutrition - record malnutrition measurements
'''

from django.db import models
from django.utils.translation import ugettext as _

#from childcount.core.models.Case import Case
from childcount.core.models.DangerSigns import DangerSigns
from childcount.core.models.Reports import PatientReport
from reporters.models import Reporter


class MuacReport(PatientReport):

    '''record malnutrition measurements'''

    MODERATE_STATUS = 1
    SEVERE_STATUS = 2
    SEVERE_COMP_STATUS = 3
    HEALTHY_STATUS = 4

    STATUS_CHOICES = (
        (MODERATE_STATUS, _('MAM')),
        (SEVERE_STATUS, _('SAM')),
        (SEVERE_COMP_STATUS, _('SAM+')),
        (HEALTHY_STATUS, _("Healthy")))

    muac = models.IntegerField(_("MUAC (mm)"), null=True, blank=True)
    height = models.IntegerField(_("Height (cm)"), null=True, blank=True)
    weight = models.FloatField(_("Weight (kg)"), null=True, blank=True)
    danger_signs = models.ManyToManyField(DangerSigns, blank=True)
    status = models.IntegerField(choices=STATUS_CHOICES, \
                            db_index=True, blank=True, null=True)

    class Meta:
        app_label = 'childcount'
        verbose_name = "Malnutrition Report"
        verbose_name_plural = "Malnutrition Reports"
        get_latest_by = 'entered_at'
        ordering = ('-entered_at',)
