'''
Births
'''

from datetime import timedelta

from django.db.models import F, Q
from django.db.models.aggregates import Sum
from django.utils.translation import ugettext as _

from indicator import Indicator
from indicator import IndicatorPercentage
from indicator import IndicatorDifference
from indicator import QuerySetType

from childcount.models import Patient
from childcount.models.reports import BirthReport
from childcount.models.reports import PregnancyReport

NAME = _("Birth")

class Total(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "total"
    short_name  = _("# Births")
    long_name   = _("Total number of patients born this period")

    @classmethod
    def _value(cls, period, data_in):
        return data_in\
            .filter(dob__range=(period.start, period.end))\
            .count()

class WeightLow(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "weight_low"
    short_name  = _("# Low-Weight Births")
    long_name   = _("Total number of patients born this period "\
                    "with weight weight < 2.5 kg")

    @classmethod
    def _value(cls, period, data_in):
        babies = data_in.filter(dob__range=(period.start, period.end))

        return BirthReport\
            .objects\
            .filter(weight__gt=0, 
                weight__lt=2.5,\
                encounter__patient__in=babies)\
            .count()

class WeightRecorded(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "weight_recorded"
    short_name  = _("# Births with Weight")
    long_name   = _("Total number of patients born this period "\
                    "with recorded weight")

    @classmethod
    def _value(cls, period, data_in):
        babies = data_in.filter(dob__range=(period.start, period.end))
        return BirthReport\
            .objects\
            .filter(weight__gt=0, 
                weight__isnull=False,\
                encounter__patient__in=babies)\
            .count()

class WeightLowPerc(IndicatorPercentage):
    type_in     = QuerySetType(Patient)

    slug        = "weight_low_perc"
    short_name  = _("% Births with Low Weight")
    long_name   = _("Percentage of patients born this period "\
                    "with recorded low weight")

    cls_num     = WeightLow
    cls_den     = WeightRecorded

class DeliveredInClinic(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "delivered_in_clinic"
    short_name  = _("# Births Delivered in Clinic")
    long_name   = _("Total number of patients born this period "\
                    "with recorded weight")

    @classmethod
    def _value(cls, period, data_in):
        babies = data_in.filter(dob__range=(period.start, period.end))
        return BirthReport\
            .objects\
            .filter(clinic_delivery=BirthReport.CLINIC_DELIVERY_YES,\
                encounter__patient__in=babies)\
            .count()

class WithLocation(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "with_location"
    short_name  = _("# Births with Location")
    long_name   = _("Total number of patients born this period "\
                    "with recorded birth location")

    @classmethod
    def _value(cls, period, data_in):
        babies = data_in.filter(dob__range=(period.start, period.end))
        return BirthReport\
            .objects\
            .filter(Q(clinic_delivery=BirthReport.CLINIC_DELIVERY_YES)|\
                Q(clinic_delivery=BirthReport.CLINIC_DELIVERY_NO))\
            .filter(encounter__patient__in=babies)\
            .count()

class DeliveredInClinicPerc(IndicatorPercentage):
    type_in     = QuerySetType(Patient)

    slug        = "delivered_in_clinic_perc"
    short_name  = _("% Births Delivered in Clinic")
    long_name   = _("% of patients born this period "\
                    "known delivered in a clinic")

    cls_num     = DeliveredInClinic
    cls_den     = WithLocation


class WithAncFour(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "with_anc_four"
    short_name  = _("# Births with ANC 4")
    long_name   = _("Total number of patients born this period "\
                    "whose mother has recorded four ANC visits by birth")

    @classmethod
    def _value(cls, period, data_in):
        babies = data_in\
            .filter(dob__range=(period.start, period.end), \
                    mother__isnull=False)

        count = 0
        for b in babies:
            p = PregnancyReport\
                .objects\
                .filter(encounter__patient=b.mother,
                    encounter__encounter_date__lt=b.dob,\
                    encounter__encounter_date__gte=b.dob-timedelta(days=9*31),\
                    anc_visits__gte=4)
            if p.count() > 0:
                p = p[0]
                count += 1

        return count
            
class WithAncFourPerc(IndicatorPercentage):
    type_in     = QuerySetType(Patient)

    slug        = "with_anc_four_perc"
    short_name  = _("% Births with ANC 4")
    long_name   = _("% of patients born this period "\
                    "whose mother had four ANC visits")

    cls_num     = WithAncFour
    cls_den     = Total

