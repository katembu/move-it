#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Report Models

CCReport
PatientReport
'''

from datetime import datetime

from django.db import models

from reporters.models import Reporter

from childcount.core.models.Patient import Patient


class CCReport(models.Model):
    '''Report Superclass'''

    created_by = models.ForeignKey(Reporter, db_index=True)
    created_on = models.DateTimeField(db_index=True)
    modified_by = models.ForeignKey(Reporter, db_index=True)
    modified_on = models.DateTimeField(db_index=True)

    class Meta:
        app_label = 'childcount'
        verbose_name = "ChildCount Report"
        verbose_name_plural = "ChildCount Reports"
        get_latest_by = 'reported_on'
        ordering = ('-reported_on',)

    def save(self, *args):
        if not self.id:
            self.created_on = self.updated_on = datetime.now()
        else:
            self.updated_on = datetime.now()
        super(CCReport, self).save(*args)


class PatientReport(CCReport):
    '''Patient reports'''

    patient = models.ForeignKey(Patient, db_index=True)
