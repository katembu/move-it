#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

# Records cases which have received measles shot

from django.db import models

from datetime import datetime

from mctc.models.reports import Report
from mctc.models.general import Case, Provider
 
class ReportMeasles(Report, models.Model):
    class Meta:
        get_latest_by = 'entered_at'
        ordering = ("-entered_at",)
        app_label = "mctc"
        verbose_name = "Measles Report"
        verbose_name_plural = "Measles Reports"
    
    case = models.ForeignKey(Case, db_index=True)
    provider = models.ForeignKey(Provider, db_index=True)
    entered_at = models.DateTimeField(db_index=True)
    taken = models.BooleanField(db_index=True)
    
    def save(self, *args):
        if not self.id:
            self.entered_at = datetime.now()
        super(ReportMeasles, self).save(*args)
        
    def zone(self):
        return self.case.zone

    @classmethod
    def is_vaccinated(cls,case):
        try:
            rpt = cls.objects.filter(case=case).latest()
            if rpt:
                return rpt.taken
            return False
        except models.ObjectDoesNotExist:
            return False
    
    @classmethod
    def get_vaccinated(cls,provider):
        try:
            rpt = cls.objects.values("case").distinct().filter(provider=provider)
            return rpt            
        except models.ObjectDoesNotExist:
            return False
    
    @classmethod
    def summary_by_zone(cls):
        try:
            rpts = cls.objects.order_by("case__zone")
            zones = []
            zcount = 0
            l = ""
            for z in rpts:
                if l == "":
                    zcount = 0
                    l = z.case.zone
                if l != z.case.zone:
                    zones.append((l.name,zcount))
                    zcount = 0
                    l = z.case.zone
                zcount += 1
            zones.append((l.name,zcount))
            return zones
        except:
            pass
