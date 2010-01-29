#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''MRDT/Malaria App Models

ReportMalaria - records reported malaria rdt tests
'''

from django.db import models
from django.utils.translation import ugettext_lazy as _

#from childcount.core.models.Case import Case
from childcount.core.models.DangerSigns import DangerSigns
from childcount.core.models.Reports import PatientReport, CCReport
from childcount.core.models.fields import RDTField, GenderField

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


class NonPatientRDTReport(CCReport, RDTField):
    class Meta:
        verbose_name = _(u"Non-patient RDT Report")
        verbose_name_plural = _(u"Non-patient RDT Reports")

    gender = models.CharField(_(u"Gender"), max_length=1, \
                              choices=GenderField.GENDER_CHOICES)

    age = models.PositiveSmallIntegerField(_(u"Age"), help_text=_(u"Age in " \
                                                                   "years"))
