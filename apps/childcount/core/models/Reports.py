#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.db import models

from reporters.models import Reporter

from childcount.core.models.Patient import Patient


class Report(models.Model):
    '''Report Superclass'''

    reporter = models.ForeignKey(Reporter, db_index=True)
    reported_on = models.DateTimeField(db_index=True)
    patient = models.ForeignKey(Patient, db_index=True)

    class Meta:
        app_label = 'childcount'
        verbose_name = "ChildCount Report"
        verbose_name_plural = "ChildCount Reports"
        get_latest_by = 'reported_on'
        ordering = ('-reported_on',)
