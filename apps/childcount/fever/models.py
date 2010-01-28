#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''MRDT/Malaria App Models

ReportMalaria - records reported malaria rdt tests
'''

from django.db import models

from datetime import datetime

from childcount.core.models.Case import Case
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

    bednet = models.BooleanField(db_index=True)
    result = models.BooleanField(db_index=True)
    danger_signs = models.ManyToManyField(DangerSigns, blank=True)
