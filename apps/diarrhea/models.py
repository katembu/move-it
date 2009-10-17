#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from datetime import datetime

from mctc.models.general import Case
from reporters.models import Reporter


# Create your Django models here, if you need them.
class DiarrheaObservation(models.Model):
    uid = models.CharField(max_length=15, primary_key=True)
    name = models.CharField(max_length=255)
    letter = models.CharField(max_length=2, unique=True)

    class Meta:
        app_label = "mctc"
        ordering = ("name",)

    def __unicode__(self):
        return self.name
        
class ReportDiarrhea(models.Model):
    
    MODERATE_STATUS         = 1
    DANGER_STATUS           = 2
    SEVERE_STATUS           = 3
    HEALTHY_STATUS          = 4
    STATUS_CHOICES = (
        (MODERATE_STATUS,   _('Moderate')),
        (DANGER_STATUS,     _('Danger')),
        (SEVERE_STATUS,     _('Severe')),
        (HEALTHY_STATUS,    _("Healthy")),
    )

    case        = models.ForeignKey(Case, db_index=True)
    reporter    = models.ForeignKey(Reporter, db_index=True)
    entered_at  = models.DateTimeField(db_index=True)
    ors         = models.BooleanField()
    days        = models.IntegerField(_("Number of days"))    
    observed    = models.ManyToManyField(DiarrheaObservation, blank=True)
    status      = models.IntegerField(choices=STATUS_CHOICES, db_index=True, blank=True, null=True)
    
    class Meta:
        app_label = "mctc"
        verbose_name = "Diarrhea Report"
        verbose_name_plural = "Diarrhea Reports"
        get_latest_by = 'entered_at'
        ordering = ("-entered_at",)

    def get_dictionary(self):
        return {
            'ors'       : "ORS: %s" % ("yes" if self.ors else "no"),
            'days'      : "Days: %d" % self.days,
            'observed'  : ", ".join([k.name for k in self.observed.all()]),
            'diagnosis' : self.get_status_display(),
            'diagnosis_msg' : self.diagnosis_msg(),
        }
                               
    def __unicode__ (self):
        return "#%d" % self.id

    def diagnose (self):
        if self.days >= 3 or self.observed.all().count() > 0:
            self.status = ReportDiarrhea.DANGER_STATUS
        else:
            self.status = ReportDiarrhea.MODERATE_STATUS

    def diagnosis_msg(self):
        if self.status == ReportDiarrhea.MODERATE_STATUS:
            msg = "MOD Patient should take ORS."
        elif self.status == ReportDiarrhea.SEVERE_STATUS:
            msg = "SEV Patient must be referred at clinic."
        elif self.status == ReportDiarrhea.DANGER_STATUS:
            msg = "DANG Patient must go to Clinic."
        else:
            msg = "HEAL Patient not in danger."
   
        return msg

    def save(self, *args):
        if not self.id:
            self.entered_at = datetime.now()
        super(ReportDiarrhea, self).save(*args)
        
