#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''ChildCount Models

Patient - Patient model
'''

from datetime import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _

from reporters.models import Reporter

#from childcount.core.models.Case import Case
from childcount.core.models.Patient import Patient
from childcount.core.models.Reports import CCReport

class Referral(models.Model):

    '''Holds Refferral details

    patient - the patient
    reporter - the reporter
    status - Open or Closed
    '''

    class Meta:
        app_label = 'childcount'

    STATUS_OPEN = 0
    STATUS_CLOSED = 1

    STATUS_CHOICES = (
        (STATUS_OPEN, _("Open")),
        (STATUS_CLOSED, _("Closed")))

    referral_id = models.CharField(max_length=30, db_index=True)
    patient = models.ForeignKey(Patient, db_index=True)
    #case = models.ForeignKey(Case, db_index=True)
    closed_by = models.ForeignKey(Reporter, db_index=True)
    status = models.IntegerField(choices=STATUS_CHOICES, \
                                      default=STATUS_OPEN)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    expires_on = models.DateTimeField(null=True, blank=True)
    closed_date = models.DateTimeField(null=True, blank=True)
    description = models.TextField()
    reports = models.ManyToManyField(CCReport)
