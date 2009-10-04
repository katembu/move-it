#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from django.utils.translation import ugettext_lazy as _

from mctc.models.reports import Report
from mctc.models.general import Provider

from datetime import datetime

class ReportDeath(Report, models.Model):    
    GENDER_CHOICES = (
        ('M', _('Male')), 
        ('F', _('Female')), 
    )
    
    LOCATION_CHOICES = (
        ('H', _('Home')), 
        ('C', _('Health Facility')),
        ('T', _('Transport - On route to Clinic')), 
    )
        
    CAUSE_CHOICES = (
        ('P', _('Pregnancy Related')), 
        ('B', _('Child Birth')),
        ('A', _('Accident')),  
        ('I', _('Illness')),
        ('S', _('Sudden Death')), 
    )
    
    first_name  = models.CharField(max_length=255, db_index=True)
    last_name   = models.CharField(max_length=255, db_index=True)
    gender      = models.CharField(max_length=1, choices=GENDER_CHOICES)
    age         = models.IntegerField(db_index=True)
    dod         = models.DateField(_('Date of Death'))
    provider    = models.ForeignKey(Provider, db_index=True)
    entered_at  = models.DateTimeField(db_index=True)
    location    = models.CharField(max_length=1, choices=LOCATION_CHOICES)
    cause       = models.CharField(max_length=1, choices=CAUSE_CHOICES)
    description   = models.CharField(max_length=255, db_index=True)
    
    class Meta:
        app_label = "deathform"
        verbose_name = "Death Report"
        verbose_name_plural = "Death Reports"
        get_latest_by = 'entered_at'
        ordering = ("-entered_at",)
        
    def __unicode__ (self):
        return "%s %s" % (self.last_name, self.first_name)
    
    def save(self, *args):
        if not self.id:
            self.entered_at = datetime.now()
        super(ReportDeath, self).save(*args)
