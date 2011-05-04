
from datetime import timedelta

from django.db.models.aggregates import Count

from django.utils.translation import ugettext as _

from indicator import Indicator
from indicator import IndicatorPercentage
from indicator import QuerySetType

from childcount.models import Patient
from childcount.models.reports import NutritionReport

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
    cls_den     = 
