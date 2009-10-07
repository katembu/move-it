#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from datetime import datetime

from django.db import models
from django.utils.translation import ugettext as _

from apps.reporters.models import *

class UnknownReporter(Exception):
    pass

class DuplicateReport(Exception):
    pass

class ErroneousDate(Exception):
    pass

class IncoherentValue(Exception):
    pass

class RDTReport(models.Model):

    reporter    = models.ForeignKey(Reporter, unique_for_date="date") # uniqueness only enforced on admin
    date        = models.DateField()
    tested      = models.PositiveIntegerField(verbose_name=_(u"Suspected malaria cases tested by the RDTs"))
    confirmed   = models.PositiveIntegerField(verbose_name=_(u"Suspected malaria cased confirmed by the RDTs"))
    treatments  = models.PositiveIntegerField(verbose_name=_(u"Treatments prescribed correlated with RDT Result"))
    used        = models.PositiveIntegerField(verbose_name=_(u"Total MRDTs used"))
    date_posted = models.DateTimeField(auto_now_add=True)
    

    def __unicode__(self):
        return _(u"%(reporter)s (%(clinic)s)/%(date)s") % \
        {'reporter': self.reporter, 'clinic':self.reporter.location.code.upper(), \
        'date': self.date.strftime("%d-%m-%Y")}

class ErroneousRDTReport(models.Model):
    
    reporter    = models.ForeignKey(Reporter, unique_for_date="date") # uniqueness only enforced on admin
    date        = models.DateField()
    tested      = models.PositiveIntegerField(verbose_name=_(u"Suspected malaria cases tested by the RDTs"))
    confirmed   = models.PositiveIntegerField(verbose_name=_(u"Suspected malaria cased confirmed by the RDTs"))
    treatments  = models.PositiveIntegerField(verbose_name=_(u"Treatments prescribed correlated with RDT Result"))
    used        = models.PositiveIntegerField(verbose_name=_(u"Total MRDTs used"))
    date_posted = models.DateTimeField(auto_now_add=True)
    date_over   = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return _(u"%(reporter)s (%(clinic)s)/%(date)s") % \
        {'reporter': self.reporter, 'clinic':self.reporter.location.code.upper(), \
        'date': self.date.strftime("%d-%m-%Y")}

    @classmethod
    def from_rdt(cls, report):
        backup  = cls(reporter=report.reporter, date=report.date, \
            tested=report.tested, confirmed=report.confirmed, treatments=report.treatments, used=report.used, date_posted=report.date_posted)
        backup.save()
        return backup

class RDTAlert(models.Model):

    STATUS_SENT = 0
    STATUS_FIXED= 1
    STATUS_CLEARED=2
    STATUS_CHOICES = (
        (STATUS_SENT, _(u"Sent")),
        (STATUS_FIXED, _(u"Honnored")),
        (STATUS_CLEARED, _(u"Cleared")),
    )

    reporter    = models.ForeignKey(Reporter)
    date_sent   = models.DateTimeField(auto_now_add=True)
    date        = models.DateField()
    status      = models.CharField(max_length=1, choices=STATUS_CHOICES,default=STATUS_SENT)

    def __unicode__(self):
        return _(u"%(reporter)s (%(clinic)s)/%(date)s") % \
        {'reporter': self.reporter, 'clinic':self.reporter.location.code.upper(), \
        'date': self.date.strftime("%d-%m-%Y")}


