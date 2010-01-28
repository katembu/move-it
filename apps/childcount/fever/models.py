#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''MRDT/Malaria App Models

ReportMalaria - records reported malaria rdt tests
'''

from django.db import models

from datetime import datetime

#from childcount.core.models.Case import Case
from childcount.core.models.DangerSigns import DangerSigns
from childcount.core.models.Reports import PatientReport

from reporters.models import Reporter


class FeverReport(PatientReport):

    '''records reported malaria rdt tests'''

    class Meta:
        get_latest_by = 'entered_at'
        ordering = ('-entered_at',)
        app_label = 'childcount'
        verbose_name = 'Fever Report'
        verbose_name_plural = 'Fever Reports'

    DANGERSIGN_CHOICES = (
         ('S', _('Signs or Yes')),
         ('N', _('No')),
         ('U', _('Unknown')))

    bednet = models.BooleanField(db_index=True)
    result = models.BooleanField(db_index=True)
    danger_signs = models.CharField(max_length=1, choices=DANGERSIGN_CHOICES)
    observations = models.ManyToManyField(DangerSigns, blank=True)
