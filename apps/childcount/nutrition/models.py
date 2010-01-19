#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Malnutrition App Models

ReportMalnutrition - record malnutrition measurements
'''

from django.db import models
from django.utils.translation import ugettext as _

from datetime import datetime

from childcount.core.models.Case import Case
from childcount.core.models.Observation import Observation
from reporters.models import Reporter


class ReportMalnutrition(models.Model):

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

    case = models.ForeignKey(Case, db_index=True)
    reporter = models.ForeignKey(Reporter, db_index=True)
    entered_at = models.DateTimeField(db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    muac = models.IntegerField(_("MUAC (mm)"), null=True, blank=True)
    height = models.IntegerField(_("Height (cm)"), null=True, blank=True)
    weight = models.FloatField(_("Weight (kg)"), null=True, blank=True)
    observed = models.ManyToManyField(Observation, blank=True)
    status = models.IntegerField(choices=STATUS_CHOICES, \
                            db_index=True, blank=True, null=True)

    class Meta:
        app_label = 'nutrition'
        verbose_name = "Malnutrition Report"
        verbose_name_plural = "Malnutrition Reports"
        get_latest_by = 'entered_at'
        ordering = ('-entered_at',)

    def save(self, *args):
        if not self.id:
            self.created_at = datetime.now()
        else:
            self.updated_at = datetime.now()
        super(ReportMalnutrition, self).save(*args)
