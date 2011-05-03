from datetime import timedelta

from django.utils.translation import ugettext as _

from indicator import Indicator
from indicator import Percentage
from indicator import IndicatorPercentage
from indicator import IndicatorDifference
from indicator import QuerySetType

from childcount.models import Patient
from childcount.models.reports import UnderOneReport

from childcount.indicators import registration

class Total(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "total"
    short_name  = _("# U1 Rpts")
    long_name   = _("Total number of under-one reports")

    @classmethod
    def _value(cls, period, data_in):
        return UnderOneReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end))\
            .count()

class Unique(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "unique"
    short_name  = _("# U1 Rpts (Uniq)")
    long_name   = _("Total number of under-one reports for distinct patients")

    @classmethod
    def _value(cls, period, data_in):
        return UnderOneReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end))\
            .values('encounter__patient')\
            .distinct()\
            .count()

class BreastFeedingKnown(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "breast_feeding_known"
    short_name  = _("#BF Known")
    long_name   = _("Total number of under-one reports for distinct patients "\
                    "where the breast-feeding status is known")

    @classmethod
    def _value(cls, period, data_in):
        Y = UnderOneReport.BREAST_YES
        N = UnderOneReport.BREAST_NO

        return UnderOneReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end),\
                breast_only__in=(Y, N))\
            .values('encounter__patient')\
            .distinct()\
            .count()

class BreastFeedingUnknown(IndicatorDifference):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "breast_feeding_unknown"
    short_name  = _("#BF Unknown")
    long_name   = _("Total number of under-one reports for distinct patients "\
                    "where the breast-feeding status is unknown")

    cls_first   = Unique
    cls_second  = BreastFeedingKnown

class UnderSixMonthsBreastFeedingOnly(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_six_months_breast_feeding_only"
    short_name  = _("<6m BF Only")
    long_name   = _("Total number of distinct patients who were under 6 months "\
                    "at the time of encounter and who are recorded as exclusively "\
                    "breast feeding")

    @classmethod
    def _value(cls, period, data_in):
        Y = UnderOneReport.BREAST_YES

        return UnderOneReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end),\
                breast_only=Y)\
            .encounter_age(0, 180)\
            .values('encounter__patient')\
            .distinct()\
            .count()

class UnderSixMonthsBreastFeedingKnown(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_six_months_breast_feeding_known"
    short_name  = _("<6m BF Known")
    long_name   = _("Total number of distinct patients who were under 6 months "\
                    "at the time of encounter and who have a known breast-feeding "\
                    "status")

    @classmethod
    def _value(cls, period, data_in):
        Y = UnderOneReport.BREAST_YES
        N = UnderOneReport.BREAST_NO

        return UnderOneReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end),\
                breast_only=(YN))\
            .encounter_age(0, 180)\
            .values('encounter__patient')\
            .distinct()\
            .count()

class UnderFiveImmunizationUpToDate(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_five_immunizaton_up_to_date"
    short_name  = _("<5y Imm Yes")
    long_name   = _("Total number of patients under 5 years at the end of the "\
                    "period whose last known immunization report was marked "\
                    "as 'up to date'")

    @classmethod
    def _value(cls, period, data_in):
        u5s = data_in.under_five(period.start, period.end)

        return UnderOneReport\
            .objects\
            .filter(encounter__patient__in=u5s,\
                encounter__encounter_date__lte=period.end,\
                immunized__in=(UnderOneReport.IMMUNIZED_YES, UnderOneReport.IMMUNIZED_NO))\
            .latest_for_patient()\
            .filter(immunized=UnderOneReport.IMMUNIZED_YES)\
            .values('encounter__patient')\
            .distinct()\
            .count()

class UnderFiveImmunizationUpToDatePerc(IndicatorPercentage):
    type_in     = QuerySetType(Patient)
    type_out    = Percentage

    slug        = "under_five_immunizaton_up_to_date_perc"
    short_name  = _("% <5y Imm Yes")
    long_name   = _("Percentage of patients under 5 years at the end of the "\
                    "period whose last known immunization report was marked "\
                    "as 'up to date'")
    
    cls_num     = UnderFiveImmunizationUpToDate
    cls_den     = registration.UnderFive


class UnderOneImmunization(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_one_immunization"
    short_name  = _("<1y Imm")
    long_name   = _("Total number of patients under 1 year old at the end "\
                    "of the period with an immunization report during the "\
                    "period")

    @classmethod
    def _value(cls, period, data_in):
        u1 = data_in.under_one(period.start, period.end)

        return UnderOneReport\
            .objects\
            .filter(encounter__patient__in=u1,\
                encounter__encounter_date__range=(period.start, period.end),\
                immunized__in=(UnderOneReport.IMMUNIZED_YES, UnderOneReport.IMMUNIZED_NO))\
            .values('encounter__patient')\
            .distinct()\
            .count()

class UnderOneImmunizationYes(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_one_immunization_yes"
    short_name  = _("<1y Imm Yes")
    long_name   = _("Total number of patients under 1 year old at the end "\
                    "of the period with an immunization report marked 'up to date' "\
                    "during the period")

    @classmethod
    def _value(cls, period, data_in):
        u1 = data_in.under_one(period.start, period.end)

        return UnderOneReport\
            .objects\
            .filter(encounter__patient__in=u1,\
                encounter__encounter_date__range=(period.start, period.end),\
                immunized=UnderOneReport.IMMUNIZED_YES)\
            .values('encounter__patient')\
            .distinct()\
            .count()
