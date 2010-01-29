#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Report Models

CCReport
PatientReport
'''

from datetime import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _

from reporters.models import Reporter

from childcount.core.models.Patient import Patient


class CCReport(models.Model):
    '''
    The highest level superclass to be inhereted by all other report classes
    '''

    created_by = models.ForeignKey(Reporter, db_index=True)
    created_on = models.DateTimeField(db_index=True, auto_now_add=True,)
    modified_by = models.ForeignKey(Reporter, db_index=True)
    modified_on = models.DateTimeField(db_index=True, auto_now=True,)

    class Meta:
        app_label = 'childcount'
        verbose_name = _("ChildCount Report")
        verbose_name_plural = _("ChildCount Reports")
        get_latest_by = 'reported_on'
        ordering = ('-reported_on',)


class PatientReport(CCReport):
    '''Patient reports'''

    patient = models.ForeignKey(Patient, db_index=True)
