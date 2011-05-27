'''
Referral Report
'''

from django.db import connection

from django.utils.translation import ugettext as _

from indicator import Indicator
from indicator import QuerySetType

from childcount.models import Patient
from childcount.models.reports import ReferralReport

NAME = _("Referral")

class Total(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "total"
    short_name  = _("Total")
    long_name   = _("Total number of referral reports")

    @classmethod
    def _value(cls, period, data_in):
        return ReferralReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=\
                    (period.start, period.end))\
            .count()

class UnderFive(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_five"
    short_name  = _("U5")
    long_name   = _("Total number of referral reports "\
                    "for under-fives")

    @classmethod
    def _value(cls, period, data_in):
        return ReferralReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=\
                    (period.start, period.end))\
            .encounter_under_five()\
            .count()

class Urgent(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "urgent"
    short_name  = _("Urgent")
    long_name   = _("Total number of urgent referral reports")

    @classmethod
    def _value(cls, period, data_in):
        A = ReferralReport.URGENCY_AMBULANCE
        E = ReferralReport.URGENCY_EMERGENCY
        B = ReferralReport.URGENCY_BASIC

        return ReferralReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end),\
                urgency__in=(A,E,B))\
            .count()
