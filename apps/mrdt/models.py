#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from django.utils.translation import ugettext as _

from datetime import datetime, date

from mctc.models.general import Case
from mctc.models.reports import Observation
from reporters.models import Reporter

class ReportMalaria(models.Model):
    class Meta:
        get_latest_by = 'entered_at'
        ordering = ("-entered_at",)
        app_label = "mrdt"
        verbose_name = "Malaria Report"
        verbose_name_plural = "Malaria Reports"
    
    case = models.ForeignKey(Case, db_index=True)
    reporter = models.ForeignKey(Reporter, db_index=True)
    entered_at = models.DateTimeField(db_index=True)
    bednet = models.BooleanField(db_index=True)
    result = models.BooleanField(db_index=True) 
    observed = models.ManyToManyField(Observation, blank=True)       

    def get_dictionary(self):
        return {
            'result': self.result,
            'result_text': self.result and "Y" or "N",
            'bednet': self.bednet,
            'bednet_text': self.bednet and "Y" or "N",
            'observed': ", ".join([k.name for k in self.observed.all()]),            
        }
        
    def zone(self):
        return self.case.zone.name
        
    def results_for_malaria_bednet(self):
        bednet = "N"
        if self.bednet is True:
           bednet = "Y"    
        return "%s"%(bednet)

    def results_for_malaria_result(self):
        result = "-"
        if self.bednet is True:
           result = "+"    
        return "%s"%(result)

    def name(self):
        return "%s %s" % (self.case.first_name, self.case.last_name)
    
    def provider_number(self):
        return self.reporter.connection().identity
        
    def save(self, *args):
        if not self.id:
            self.entered_at = datetime.now()
        super(ReportMalaria, self).save(*args)
        
    @classmethod
    def count_by_provider(cls,reporter, duration_end=None,duration_start=None):
        if reporter is None:
            return None
        try:
            if duration_start is None or duration_end is None:
                return cls.objects.filter(reporter=reporter).count()
            return cls.objects.filter(entered_at__lte=duration_end, entered_at__gte=duration_start).filter(reporter=reporter).count()
        except models.ObjectDoesNotExist:
            return None
    
    @classmethod
    def num_reports_by_case(cls, case=None):
        if case is None:
            return None
        try:
            return cls.objects.filter(case=case).count()
        except models.ObjectDoesNotExist:
            return None
    @classmethod
    def days_since_last_mrdt(cls, case):
        today = date.today()
        
        logs = cls.objects.filter(entered_at__lte=today, case=case).reverse()
        if not logs:
            return ""
        return (today - logs[0].entered_at.date()).days

