from datetime import timedelta

import numpy

from django.utils.translation import ugettext as _
from django.db import connection

from indicator import Indicator
from indicator import IndicatorPercentage
from indicator import IndicatorDifference
from indicator import QuerySetType

from childcount.models.reports import FollowUpReport
from childcount.models.reports import ReferralReport
from childcount.models import Patient

NAME = _("Follow Up")

DELTA_START_ON_TIME     = timedelta(seconds=60*60*18)   # 18 hrs
DELTA_START_LATE        = timedelta(seconds=60*60*72)   # 72 hrs
DELTA_START_NEVER       = timedelta(seconds=60*60*24*7) # 7 days

class Total(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "total"
    short_name  = _("# FUP")
    long_name   = _("Total follow-up reports this period")

    @classmethod
    def _value(cls, period, data_in):
        return FollowUpReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end))\
            .count()

def _eligible(period, data_in):
    A = ReferralReport.URGENCY_AMBULANCE
    B = ReferralReport.URGENCY_BASIC
    E = ReferralReport.URGENCY_EMERGENCY

    return ReferralReport\
        .objects\
        .filter(encounter__patient__in=data_in,\
            encounter__encounter_date__range=(period.start, period.end),\
            urgency__in=(A,E,B))

class Eligible(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "eligible"
    short_name  = _("Eligible")
    long_name   = _("Total number of referrals eligible for "\
                    "a follow-up visit during this period")

    @classmethod
    def _value(cls, period, data_in):
        return _eligible(period, data_in).count()

def _follow_up_between(period, data_in, delta_start, delta_end):
    elig = _eligible(period, data_in)
    elig_pks = [row[0] for row in elig\
        .values_list('encounter__patient__pk')\
        .distinct()]

    count = 0
    # For each patient who is eligible for follow up...
    for pk in elig_pks:
        patient_elig = elig\
            .filter(encounter__patient__pk=pk)\
            .order_by('encounter__encounter_date')

        print "Considering patient %s" % Patient.objects.get(pk=pk)

        # Go through referral reports from earliest
        # to latest
        start_date = patient_elig[0].encounter.encounter_date
        for ref in patient_elig:
            start_date = max(start_date, ref.encounter.encounter_date)

            print "\tReferred on: %s" % ref.encounter.encounter_date
            f = FollowUpReport\
                .objects\
                .filter(encounter__patient__pk=ref.encounter.patient.pk,
                    encounter__encounter_date__gt=start_date+delta_start,
                    encounter__encounter_date__lte=start_date+delta_end)

            if f.count() > 0:
                print "\t\tFollowed on %s" % f[0].encounter.encounter_date
                count += 1

            start_date += delta_end

    return count

'''
def _follow_up_between(period, data_in, delta_start, delta_end):
    elig_rpts = _eligible(period, data_in)
    elig = [e[0] for e in elig_rpts.values_list('encounter__patient__pk')]

    f = FollowUpReport\
        .objects\
        .filter(encounter__patient__in=elig,\
            encounter__encounter_date__gte=period.start,\
            encounter__encounter_date__lte=period.end+DELTA_START_NEVER)

    count = 0
    for e in elig_rpts:
        fup_start = e.encounter.encounter_date + delta_start
        fup_end = e.encounter.encounter_date + delta_end

        #print "! %s" % e.encounter.encounter_date
        r = f.filter(encounter__patient=e.encounter.patient,\
                encounter__encounter_date__gt=fup_start, 
                encounter__encounter_date__lte=fup_end)
        if r.count():
            count += 1
        #    print "@ %s" % r[0].encounter.encounter_date

    return count
'''


class Late(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "late"
    short_name  = _("Late")
    long_name   = _("Total number of late follow-up visits "\
                    "(after 3 days but before 7 days) during this period")

    @classmethod
    def _value(cls, period, data_in):
        return _follow_up_between(period, data_in,\
            DELTA_START_LATE, DELTA_START_NEVER)

class OnTime(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "on_time"
    short_name  = _("On-Time")
    long_name   = _("Total number of on-time follow-up visits "\
                    "between (18 and 72 hours) "\
                    "during this period")

    @classmethod
    def _value(cls, period, data_in):
        return _follow_up_between(period, data_in,\
            DELTA_START_ON_TIME, DELTA_START_LATE)


class OnTimePerc(IndicatorPercentage):
    type_in     = QuerySetType(Patient)

    slug        = "on_time_perc"
    short_name  = _("% On-Time")
    long_name   = _("Percentage of referrals with an "\
                    "on-time follow-up visit (between "\
                    "18 and 72 hours)")

    cls_num     = OnTime
    cls_den     = Eligible

class _NotOnTime(IndicatorDifference):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "_not_on_time"

    cls_first   = Eligible
    cls_second  = OnTime
    
class Never(IndicatorDifference):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "never"
    short_name  = _("Never")
    long_name   = _("Referral cases that were never followed "\
                    "up (or were followed after seven days)")
    cls_first   = _NotOnTime
    cls_second  = Late
    
class MedianDays(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = float

    slug        = "median_days"
    short_name  = _("Days")
    long_name   = _("Median number of days for follow-up")
   
    @classmethod
    def _value(cls, period, data_in):
        elig_rpts = _eligible(period, data_in)
        elig = [e[0] for e in elig_rpts.values_list('encounter__patient__pk')]

        f = FollowUpReport\
            .objects\
            .filter(encounter__patient__in=elig,\
                encounter__encounter_date__gte=period.start,\
                encounter__encounter_date__lte=period.end+DELTA_START_NEVER)

        lst = []
        for e in elig_rpts:
            fup_start = e.encounter.encounter_date + DELTA_START_ON_TIME

            r = f\
                .filter(encounter__patient=e.encounter.patient,\
                    encounter__encounter_date__gt=fup_start)\
                .order_by('encounter__encounter_date')
            
            if r.count():
                lst.append(float((r[0].encounter.encounter_date -\
                    e.encounter.encounter_date).days))
            else:
                lst.append(float('inf'))

        return numpy.median(lst)
