from datetime import timedelta

from django.utils.translation import ugettext as _
from django.db import connection

from indicator import Indicator
from indicator import IndicatorPercentage
from indicator import QuerySetType

from childcount.models.reports import PregnancyReport
from childcount.models.reports import HouseholdVisitReport
from childcount.models.reports import ReferralReport
from childcount.models import Patient

class Total(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "total"
    short_name  = _("# Preg")
    long_name   = _("Total women who are pregnant "\
                    "at the end of this period")

    @classmethod
    def _value(cls, period, data_in):
        return data_in\
            .pregnant(period.start, period.end)\
            .count()

class MonthFour(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "month_four"
    short_name  = _("# Preg 4m")
    long_name   = _("Total women who are more than 4 months pregnant "\
                    "at the end of this period")

    @classmethod
    def _value(cls, period, data_in):
        return data_in\
            .pregnant_months(period.start, period.end,\
                4.0, 9.5, False, False)\
            .count()

class MonthEight(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "month_eight"
    short_name  = _("# Preg 8m")
    long_name   = _("Total women who are more than 8 months pregnant "\
                    "at the end of this period")

    @classmethod
    def _value(cls, period, data_in):
        return data_in\
            .pregnant_months(period.start, period.end,\
                8.0, 9.5, False, False)\
            .count()

class Coverage(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "coverage"
    short_name  = _("Cov")
    long_name   = _("Number of women who are "\
                    "pregnant at the end of this period "\
                    "getting a visit in the six weeks before the "\
                    "end of this period")

    @classmethod
    def _value(cls, period, data_in):
        pregs = data_in.pregnant(period.start, period.end)

        return PregnancyReport\
            .objects\
            .filter(encounter__patient__in=pregs,\
                    encounter__encounter_date__range=
                                    (period.end - timedelta(6*7), period.end))\
            .values('encounter__patient__pk')\
            .distinct()\
            .count()

class CoveragePerc(IndicatorPercentage):
    type_in     = QuerySetType(Patient)

    slug        = "coverage_perc"
    short_name  = _("%Cov")
    long_name   = _("Percentage of women who are "\
                    "pregnant at the end of this period "\
                    "who got a visit in the six weeks before the "\
                    "end of this period")
    
    cls_num     = Coverage
    cls_den     = Total

class AncFourByDelivery(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "anc_four_by_delivery"
    short_name  = _("Birth 4 ANC")
    long_name   = _("Number of women who delivered during this "\
                    "time period who had four ANC visits")

    @classmethod
    def _value(cls, period, data_in):
        deliv = data_in.delivered(period.start, period.end)

        return PregnancyReport\
            .objects\
            .filter(encounter__patient__in=deliv,
                encounter__encounter_date__range=(period.start, period.end),
                anc_visits__gte=4)\
            .values('encounter__patient')\
            .distinct()\
            .count()

class AncZeroByMonthFour(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "anc_zero_by_month_four"
    short_name  = _(">4m =0 ANC")
    long_name   = _("Number of women more than four months "\
                    "pregnant at the end of this period who "\
                    "have never had an ANC visit")

    @classmethod
    def _value(cls, period, data_in):
        after4 = data_in.pregnant_months(period.start, period.end,\
            4.0, 9.0, False, False)

        return PregnancyReport\
            .objects\
            .filter(anc_visits=0,\
                encounter__patient__in=after4,
                encounter__encounter_date__lte=period.end,
                encounter__encounter_date__gte=period.end-timedelta(9*30))\
            .values('encounter__patient')\
            .distinct()\
            .count()


class AncFourByMonthEight(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "anc_four_by_month_eight"
    short_name  = _(">8m >=4 ANC")
    long_name   = _("Number of women more than eight months "\
                    "pregnant at the end of this period who "\
                    "have had at least eight ANC visits")

    @classmethod
    def _value(cls, period, data_in):
        after8 = data_in.pregnant_months(period.start, period.end,\
            8.0, 9.5, False, False)

        return PregnancyReport\
            .objects\
            .filter(anc_visits__gte=4,\
                encounter__patient__in=after8,
                encounter__encounter_date__lte=period.end,
                encounter__encounter_date__gte=period.end-timedelta(9*30))\
            .values('encounter__patient')\
            .distinct()\
            .count()

class Referred(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "referred"
    short_name  = _("Referred")
    long_name   = _("Number of women pregnant at the end "\
                    "of this period who were referred with referral "\
                    "code A, E, B")

    @classmethod
    def _value(cls, period, data_in):
        A = ReferralReport.URGENCY_AMBULANCE
        B = ReferralReport.URGENCY_BASIC
        E = ReferralReport.URGENCY_EMERGENCY

        return data_in\
            .pregnant(period.start, period.end)\
            .filter(encounter__ccreport__referralreport__encounter__encounter_date__range=\
                (period.start, period.end),\
                encounter__ccreport__referralreport__urgency__in=(A,B,E))\
            .count()


        
        return PregnancyReport\
            .objects\
            .filter(anc_visits__gte=4,\
                encounter__patient__in=after8,
                encounter__encounter_date__lte=period.end,
                encounter__encounter_date__gte=period.end-timedelta(9*30))\
            .values('encounter__patient')\
            .distinct()\
            .count()

