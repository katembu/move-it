#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.contrib import admin
from django.db import models
from django.utils.translation import ugettext_lazy as _

from apps.reporters.models import *

class Configuration(models.Model):

    id          = models.PositiveIntegerField(primary_key=True, default=1,editable=False)
    low_stock_level = models.PositiveIntegerField()

    def __unicode__(self):
        return "Configuration"

class RDTStockAlert(models.Model):

    STATUS_SENT = 0
    STATUS_FIXED= 1
    STATUS_CLEARED=2
    STATUS_OBSOLETE=3
    STATUS_CHOICES = (
        (STATUS_SENT, _(u"Sent")),
        (STATUS_FIXED, _(u"Honnored")),
        (STATUS_CLEARED, _(u"Cleared")),
        (STATUS_OBSOLETE, _(u"Obsolete")),
    )

    reporter    = models.ForeignKey(Reporter)
    date_sent   = models.DateTimeField(auto_now_add=True)
    quantity    = models.PositiveIntegerField()
    status      = models.CharField(max_length=1, choices=STATUS_CHOICES,default=STATUS_SENT)

    def __unicode__(self):
        return _(u"%(reporter)s (%(clinic)s) (%(qty)s)/%(date)s") % \
        {'reporter': self.reporter, 'clinic':self.reporter.location.code.upper(), \
        'date': self.date_sent.strftime("%d-%m-%Y"), 'qty': self.quantity}
