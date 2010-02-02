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
        verbose_name = _(u"Case")
        verbose_name_plural = _(u"Cases")

    STATUS_OPEN = 0
    STATUS_CLOSED = 1

    STATUS_CHOICES = (
        (STATUS_OPEN, _(u"Open")),
        (STATUS_CLOSED, _(u"Closed")))

    TYPE_PREGNANCY = 0
    TYPE_MALNUTRITION = 1
    TYPE_MALARIA = 2
    TYPE_DIARRHEA = 3

    TYPE_CHOICES = (
        (TYPE_PREGNANCY, _(u"Pregnancy")),
        (TYPE_MALNUTRITION, _(u"Malnutrition")),
        (TYPE_MALARIA, _(u"Malaria")),
        (TYPE_DIARRHEA, _(u"Diarrhea")))

    patient = models.ForeignKey(Patient, verbose_name=_(u"Patient"), \
                                db_index=True)

    status = models.SmallIntegerField(_(u"Status"), choices=STATUS_CHOICES, \
                                      default=STATUS_OPEN)
    expires_on = models.DateTimeField(_(u"Expires on"), null=True, blank=True)
    type = models.IntegerField(_(u"Type of case"), choices=TYPE_CHOICES, \
                                      default=TYPE_CHOICES)
    created_on = models.DateTimeField(_(u"Created on"), auto_now_add=True)
    updated_on = models.DateTimeField(_(u"Updated on"), auto_now=True)
