#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''MRDT/Malaria App Models

ReportMalaria - records reported malaria rdt tests
'''

from django.db import models

from datetime import datetime

from childcount.core.models.Case import Case
from childcount.core.models.Observation import Observation
from reporters.models import Reporter


class ReportMalaria(models.Model):

    '''records reported malaria rdt tests'''

    class Meta:
        get_latest_by = 'entered_at'
        ordering = ('-entered_at',)
        app_label = 'childcount'
        verbose_name = 'Malaria Report'
        verbose_name_plural = 'Malaria Reports'

    case = models.ForeignKey(Case, db_index=True)
    reporter = models.ForeignKey(Reporter, db_index=True)
    entered_at = models.DateTimeField(db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    bednet = models.BooleanField(db_index=True)
    result = models.BooleanField(db_index=True)
    observed = models.ManyToManyField(Observation, blank=True)

    def save(self, *args):
        if not self.id:
            self.created_at = datetime.now()
        else:
            self.updated_at = datetime.now()
        super(ReportMalaria, self).save(*args)
