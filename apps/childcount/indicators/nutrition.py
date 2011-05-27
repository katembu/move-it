
from datetime import timedelta

from django.db.models import Q
from django.db.models.aggregates import Count

from django.utils.translation import ugettext as _

from indicator import Indicator
from indicator import IndicatorPercentage
from indicator import IndicatorDifference
from indicator import QuerySetType

from childcount.models import Patient
from childcount.models.reports import NutritionReport

from childcount.indicators import registration

NAME = _("Nutrition")

def _nutrition_reports(period, data_in):
    return NutritionReport\
            .objects\
            .filter(encounter__encounter_date__range=(period.start, period.end),\
                encounter__patient__in=data_in,\
                muac__gt=0)\
            .encounter_muac_eligible()
         
class Total(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "total"
    short_name  = _("Total")
    long_name   = _("Total number of non-empty nutrition reports")

    @classmethod
    def _value(cls, period, data_in):
        return _nutrition_reports(period, data_in).count()

class Unique(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "unique"
    short_name  = _("Unique")
    long_name   = _("Total number of patients with a non-empty nutrition report "\
                    "this period")

    @classmethod
    def _value(cls, period, data_in):
        return _nutrition_reports(period, data_in)\
            .values('encounter__patient')\
            .distinct()\
            .count()

class UniqueNinetyDays(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "unique_ninety_days"
    short_name  = _("Unique")
    long_name   = _("Total number of patients with a non-empty nutrition report "\
                    "in the 90 days up to the end of the time period")

    @classmethod
    def _value(cls, period, data_in):
        m = data_in.muac_eligible(period.start, period.end)
        
        return NutritionReport\
            .objects\
            .filter(encounter__patient__in=m,\
                encounter__encounter_date__range=\
                    (period.end-timedelta(days=90), period.end),\
                muac__gt=0)\
            .values('encounter__patient')\
            .distinct()\
            .count()

class CoveragePerc(IndicatorPercentage):
    type_in     = QuerySetType(Patient)

    slug        = "coverage_perc"
    short_name  = _("%Cov")
    long_name   = _("Percentage of patients eligible for MUAC who "\
                    "had a MUAC taken in the 90 days before the end of "\
                    "the period")

    cls_num     = UniqueNinetyDays
    cls_den     = registration.MuacEligible

def _muac_ninety_days(period, data_in):
    m = data_in.muac_eligible(period.start, period.end)
    
    return NutritionReport\
        .objects\
        .filter(encounter__encounter_date__range=\
                        (period.end-timedelta(days=90), period.end),\
                muac__gt=0)\
        .latest_for_patient()\
        .filter(encounter__patient__in=m)

class Sam(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "sam"
    short_name  = _("SAM")
    long_name   = _("Total number of patients with a nutrition report "\
                    "in the 90 days up to the end of the time period "\
                    "with a MUAC<110 or Oedema=Yes")

    @classmethod
    def _value(cls, period, data_in):
        return _muac_ninety_days(period, data_in)\
            .filter(Q(muac__lt=110)|Q(oedema=NutritionReport.OEDEMA_YES))\
            .values('encounter__patient')\
            .distinct()\
            .count()

class Mam(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "mam"
    short_name  = _("SAM")
    long_name   = _("Total number of patients with a nutrition report "\
                    "in the 90 days up to the end of the time period "\
                    "with a 110<=MUAC<125 and Oedema=No")

    @classmethod
    def _value(cls, period, data_in):
        return _muac_ninety_days(period, data_in)\
            .filter(muac__gte=110, muac__lt=125, oedema=NutritionReport.OEDEMA_NO)\
            .values('encounter__patient')\
            .distinct()\
            .count()

class SamOrMam(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "sam_or_mam"
    short_name  = _("SAM/MAM")
    long_name   = _("Total number of patients with a nutrition report "\
                    "in the 90 days up to the end of the time period "\
                    "with a 0<MUAC<125 or Oedema=Yes")

    @classmethod
    def _value(cls, period, data_in):
        return _muac_ninety_days(period, data_in)\
            .filter(Q(muac__lt=125)|Q(oedema=NutritionReport.OEDEMA_YES))\
            .values('encounter__patient')\
            .distinct()\
            .count()

class Known(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "known"
    short_name  = _("w/MUAC")
    long_name   = _("Total number of MUAC-eligible patients with a non-empty nutrition report "\
                    "in the 90 days up to the end of the time period")

    @classmethod
    def _value(cls, period, data_in):
        return _muac_ninety_days(period, data_in).count()

class Unknown(IndicatorDifference):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "unknown"
    short_name  = _("w/o MUAC")
    long_name   = _("Total number of MUAC-eligible patients with no report MUAC "\
                    "measurement in the past 90 days before the end of the "\
                    "period")
  
    cls_first   = registration.MuacEligible
    cls_second  = Known

class Healthy(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "healthy"
    short_name  = _("MUAC => 125")
    long_name   = _("Total number of MUAC-eligible patients with a nutrition report "\
                    "reporting a MUAC >= 125 "\
                    "in the 90 days up to the end of the time period")

    @classmethod
    def _value(cls, period, data_in):
        return _muac_ninety_days(period, data_in)\
            .filter(muac__gte=125)\
            .exclude(oedema=NutritionReport.OEDEMA_YES)\
            .count()


