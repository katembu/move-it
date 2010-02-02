#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Child specific models

BirthReport
'''

from django.db import models
from django.utils.translation import ugettext_lazy as _

from childcount.core.models.Reports import PatientReport

class BirthReport(PatientReport):

    class Meta:
        app_label = 'childcount'
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
        
    SMALL_YES = 'Y'
    SMALL_NO = 'N'
    SMALL_UNKOWN = 'U'
    SMALL_CHOICES = (
        (SMALL_YES, _(u"Yes")),
        (SMALL_NO, _(u"No")),
        (SMALL_UNKOWN, _(u"Unknown")))
    
    clinic_delivery = models.CharField(_(u"Clinic delivery"), max_length=1, \
                                       choices=CLINIC_DELIVERY_CHOICES, \
                                       help_text=_(u"Was the baby born in " \
                                                    "a health facility?"))

    bcg = models.CharField(_(u"BCG immunisation"), max_length=1, \
                           choices=CLINIC_DELIVERY_CHOICES, \
                           help_text=_(u"Has the baby received the BCG " \
                                        "vaccination?"))
                                        
    small = models.CharField(_(u"Small baby"), max_length=1, \
                             choices=SMALL_CHOICES, \
                             help_text=_(u"Is the baby small?"))


class NewbornReport(PatientReport):
    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Newborn Report")
        verbose_name_plural = _(u"Newborn Reports")

    BREAST_YES = 'Y'
    BREAST_NO = 'N'
    BREAST_UNKOWN = 'U'
    BREAST_CHOICES = (
        (BREAST_YES, _(u"Yes")),
        (BREAST_NO, _(u"No")),
        (BREAST_UNKOWN, _(u"Unkown")))

    clinic_vists = models.PositiveSmallIntegerField(_(u"Clinic visits"), \
                                               help_text=_(u"Number of " \
                                                            "clinic visits " \
                                                            "since birth"))                                          

    breast_only = models.CharField(_(u"Breast feeding Only"), max_length=1, \
                                   choices=BREAST_CHOICES, \
                                   help_text=_(u"Does the mother breast " \
                                                "feed only?"))

class ChildReport(PatientReport):
    class Meta:
        app_label = 'childcount'
        verbose_name = _(u"Child Report")
        verbose_name_plural = _(u"Child Reports")

    FEVER_YES = 'F'
    FEVER_NO = 'N'
    FEVER_UNKOWN = 'U'
    FEVER_CHOICES = (
        (FEVER_YES, _(u"Yes")),
        (FEVER_NO, _(u"No")),
        (FEVER_UNKOWN, _(u"Unknown")))

    DIARRHEA_YES = 'D'
    DIARRHEA_NO = 'N'
    DIARRHEA_UNKOWN = 'U'
    DIARRHEA_CHOICES = (
        (DIARRHEA_YES, _(u"Yes")),
        (DIARRHEA_NO, _(u"No")),
        (DIARRHEA_UNKOWN, _(u"Unknown")))
    
    fever = models.CharField(_(u"Fever"), max_length=1, \
                             choices=FEVER_CHOICES, \
                             help_text=_(u"Has the child had a fever in the " \
                                          "past 3 days? "))

    diarrhea = models.CharField(_(u"Diarrhea"), max_length=1, \
                                choices=DIARRHEA_CHOICES, \
                                help_text=_(u"Has the child had diarrhea in " \
                                             "the past 24 hours? "))
