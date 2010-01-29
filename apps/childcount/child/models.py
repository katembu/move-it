#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Child specific models

BirthReport
'''

from django.db import models
from django.utils.translation import ugettext_lazy as _

from childcount.core.models.Reports import PatientReport
from childcount.core.models.fields import DangerSignsField


class BirthReport(PatientReport, DangerSignsField):
    class Meta:
        verbose_name = _(u"Birth Report")
        verbose_name_plural = _(u"Birth Reports")

    CLINIC_DELIVERY_YES = 'Y'
    CLINIC_DELIVERY_NO = 'N'
    CLINIC_DELIVERY_UNKOWN = 'U'
    CLINIC_DELIVERY_CHOICES = (
        (CLINIC_DELIVERY_YES, _(u"Yes")),
        (CLINIC_DELIVERY_NO, _(u"No")),
        (CLINIC_DELIVERY_UNKOWN, _(u"Unknown")))

    BCG_YES = 'Y'
    BCG_NO = 'N'
    BCG_UNKOWN = 'U'
    BCG_CHOICES = (
        (BCG_YES, _(u"Yes")),
        (BCG_NO, _(u"No")),
        (BCG_UNKOWN, _(u"Unknown")))
    
    clinic_delivery = models.CharField(_(u"Clinic delivery"), max_length=1, \
                                       choices=CLINIC_DELIVERY_CHOICES, \
                                       help_text=_(u"Was the baby born in " \
                                                    "a health facility?"))

    bcg = models.CharField(_(u"BCG immunisation"), max_length=1, \
                           choices=CLINIC_DELIVERY_CHOICES, \
                           help_text=_(u"Has the baby received the BCG " \
                                        "vaccination?"))


class NewbornReport(PatientReport, DangerSignsField):
    class Meta:
        verbose_name = _(u"Newborn Report")
        verbose_name_plural = _(u"Newborn Reports")

    clinic_vists = models.PositiveSmallIntegerField(_(u"Clinic visits"), \
                                               help_text=_(u"Number of " \
                                                            "clinic visits " \
                                                            "since birth"))
