#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''ChildCount Models

Case - Case/Encounter model
'''

from django.db import models
from django.utils.translation import ugettext_lazy as _
from datetime import datetime

from reporters.models import Reporter

from childcount.core.models.Patient import Patient


class Case(models.Model):

    '''Holds Encounter details

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

    TYPE_MUAC = 0
    TYPE_FEVER = 1

    TYPE_CHOICES = (
        (TYPE_MUAC, _("Malnutrition")),
        (TYPE_FEVER, _("FEVER")))

    patient = models.ForeignKey(Patient, db_index=True)
    #reporter = models.ForeignKey(Reporter, db_index=True)
    status = models.IntegerField(choices=STATUS_CHOICES, \
                                      default=STATUS_OPEN)
    expires_on = models.DateTimeField(null=True, blank=True)
    type = models.IntegerField(choices=TYPE_CHOICES, \
                                      default=TYPE_MUAC)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CaseNote(models.Model):

    ''' Holds notes for Cases

        case - Case object
        reporter - reporter
        created_at - time created
        text - stores the note text
    '''

    case = models.ForeignKey(Case, related_name='notes', db_index=True)
    reporter = models.ForeignKey(Reporter, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    text = models.TextField()

    class Meta:
        app_label = 'childcount'
