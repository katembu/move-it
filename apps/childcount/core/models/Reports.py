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

    created_by = models.ForeignKey(Reporter, verbose_name=_(u"Created by"), \
                                   related_name='created_report',
                                   help_text=_(u"Reporter that created the " \
                                                "report"))

    created_on = models.DateTimeField(_(u"Created on"), auto_now_add=True, \
                                      help_text=_(u"When the report was " \
                                                   "created"))

    modified_by = models.ForeignKey(Reporter, verbose_name=_(u"Modified by"), \
                                    related_name='modified_report',
                                    null=True, blank=True, \
                                    help_text=_(u"Reporter that last " \
                                                 "modified the report"))

    modified_on = models.DateTimeField(_(u"Modified on"), auto_now=True, \
                                       null=True, blank=True, \
                                       help_text=_(u"When the report was " \
                                                    "last modified"))

    class Meta:
        app_label = 'childcount'
        verbose_name = _("ChildCount Report")
        verbose_name_plural = _("ChildCount Reports")
        get_latest_by = 'reported_on'
        ordering = ('-reported_on',)


class PatientReport(CCReport):
    '''Patient reports'''

    patient = models.ForeignKey(Patient, verbose_name=_(u"Patient"))


class DeathReport(PatientReport):
    class Meta:
        verbose_name = _(u"Death Report")
        verbose_name_plural = _(u"Death Reports")

    death_date = models.DateField(_(u"Date of death"), \
                                  help_text=_(u"The date of the death " \
                                               "accurate to within the month"))


class PatientRegistrationReport(PatientReport):
    pass
