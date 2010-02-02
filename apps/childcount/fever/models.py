#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''MRDT/Malaria App Models

ReportMalaria - records reported malaria rdt tests
'''

from django.db import models
from django.utils.translation import ugettext_lazy as _

from reporters.models import Reporter

from childcount.core.models.Reports import PatientReport, CCReport
from childcount.core.models.SharedFields import RDTField, GenderField


class FeverReport(PatientReport, RDTField):

    '''records reported malaria rdt tests'''

    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Fever Report")
        verbose_name_plural = _(u"Fever Reports")

class NonPatientRDTReport(CCReport, RDTField, GenderField):
    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Non-patient RDT Report")
        verbose_name_plural = _(u"Non-patient RDT Reports")

    age = models.PositiveSmallIntegerField(_(u"Age"), help_text=_(u"Age in " \
                                                                   "years"))
