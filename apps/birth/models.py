#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db import models

from mctc.models.reports import Report
from mctc.models.general import Provider, Case

from datetime import datetime

def _(txt): return txt

class ReportBirth(Report, models.Model):    
        
    LOCATION_CHOICES = (
        ('H', _('Home')), 
        ('C', _('Health Facility')),
        ('T', _('Transport - On route to Clinic')),         
        ('O', _('Other')), 
    )
    
    case            = models.ForeignKey(Case, db_index=True, null=False)
    weight          = models.FloatField(db_index=True, null=False)
    location        = models.CharField(max_length=1, choices=LOCATION_CHOICES)
    complications   = models.CharField(max_length=255, db_index=True)
    provider    = models.ForeignKey(Provider, db_index=True)    
    entered_at  = models.DateTimeField(db_index=True)
    
    
    class Meta:
        app_label = "birth"
        verbose_name = "Birth Report"
        verbose_name_plural = "Birth Reports"
        get_latest_by = 'entered_at'
        ordering = ("-entered_at",)
        
    def __unicode__ (self):
        return "%s %s" % (self.last_name, self.first_name)
    
    def save(self, *args):
        if not self.id:
            self.entered_at = datetime.now()
        super(ReportBirth, self).save(*args)
    
    def get_location(self):
        locations = dict([ (k, v) for (k,v) in self.LOCATION_CHOICES])
        return locations.get(self.location, None)
    
    def display_name(self):
        return u"%s %s"%(self.case.first_name, self.case.last_name)
    display_name.short_description = "Name"
    
    def display_dob(self):
        return u"%s"%self.case.dob.strftime("%d/%m/%y")
    display_dob.short_description = "Date of Birth"