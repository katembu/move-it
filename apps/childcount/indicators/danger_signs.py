
from datetime import timedelta

from django.db.models.aggregates import Count

from django.utils.translation import ugettext as _

from indicator import Indicator
from indicator import QuerySetType

from childcount.models import Patient
from childcount.models.reports import DangerSignsReport
from childcount.models.reports import FeverReport
from childcount.models.reports import FollowUpReport

class Total(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "total"
    short_name  = _("Total")
    long_name   = _("Total number of danger signs reports")

    @classmethod
    def _value(cls, period, data_in):
        return DangerSignsReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end))\
            .count()

class UnderFiveDiarrhea(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_five_diarrhea"
    short_name  = _("U5 Diarrhea")
    long_name   = _("Total number of danger signs reports "\
                    "for U5s with diarrhea")

    @classmethod
    def _value(cls, period, data_in):
        return DangerSignsReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end),\
                danger_signs__code='DR')\
            .encounter_under_five()\
            .count()

# This function returns a Patient DangerSignsReport QuerySet.
# We can reuse this code across Indicator classes.
def _under_five_diarrhea_uncomplicated(period, data_in):
    return DangerSignsReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end))\
            .annotate(n_signs=Count('danger_signs'))\
            .filter(danger_signs__code='DR', n_signs=1)\
            .encounter_under_five()

class UnderFiveDiarrheaUncomplicated(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_five_diarrhea_uncomplicated"
    short_name  = _("U5 Dr Uncompl")
    long_name   = _("Total number of danger signs reports "\
                    "for U5s with uncomplicated diarrhea")

    @classmethod
    def _value(cls, period, data_in):
        return _under_five_diarrhea_uncomplicated(period, data_in).count()

def _under_five_diarrhea_uncomplicated_getting(period, data_in, drug_code):
    return _under_five_diarrhea_uncomplicated(period, data_in)\
        .filter(encounter__ccreport__medicinegivenreport__medicines__code=drug_code)

class UnderFiveDiarrheaUncomplicatedGettingOrs(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_five_diarrhea_uncomplicated_getting_ors"
    short_name  = _("U5 Dr Uncompl w/ ORS")
    long_name   = _("Total number of danger signs reports "\
                    "for U5s with uncomplicated diarrhea "\
                    "who were treated with ORS")

    @classmethod
    def _value(cls, period, data_in):
        return _under_five_diarrhea_uncomplicated_getting(period, data_in, 'R').count()

class UnderFiveDiarrheaUncomplicatedGettingZinc(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_five_diarrhea_uncomplicated_getting_zinc"
    short_name  = _("U5 Dr Uncompl w/ Zinc")
    long_name   = _("Total number of danger signs reports "\
                    "for U5s with uncomplicated diarrhea "\
                    "who were treated with Zinc")

    @classmethod
    def _value(cls, period, data_in):
        return _under_five_diarrhea_uncomplicated_getting(period, data_in, 'Z').count()

def _under_five_fever_uncomplicated(period, data_in):
    fever = DangerSignsReport\
        .objects\
        .filter(encounter__encounter_date__range=(period.start, period.end),\
            encounter__patient__in=data_in)\
        .annotate(n_signs=Count('danger_signs'))\
        .filter(danger_signs__code='FV')\
        .encounter_under_five()

    fever_only = fever.filter(n_signs=1)
    fever_diarrhea = fever.filter(n_signs=2, danger_signs__code='DR')

    return (fever_only|fever_diarrhea)

class UnderFiveFeverUncomplicated(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_five_fever_uncomplicated"
    short_name  = _("U5 Fv Uncompl")
    long_name   = _("Total number of danger signs reports "\
                    "for U5s with uncomplicated fever")

    @classmethod
    def _value(cls, period, data_in):
        return _under_five_fever_uncomplicated(period, data_in).count()

class UnderFiveFeverUncomplicatedRdt(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_five_fever_uncomplicated_rdt"
    short_name  = _("U5 Fv Uncompl RDT")
    long_name   = _("Total number of danger signs reports "\
                    "for U5s with uncomplicated fever with "\
                    "an RDT result")

    @classmethod
    def _value(cls, period, data_in):
        rpts = _under_five_fever_uncomplicated(period, data_in)

        N = FeverReport.RDT_NEGATIVE
        P = FeverReport.RDT_POSITIVE
        U = FeverReport.RDT_UNKNOWN

        return rpts\
            .filter(encounter__ccreport__feverreport__rdt_result__in=(N, P, U))\
            .count()

def _under_five_fever_uncomplicated_rdt_value(period, data_in, value):
    Y = FeverReport.RDT_POSITIVE
    N = FeverReport.RDT_NEGATIVE
    U = FeverReport.RDT_UNKNOWN

    if value not in (Y,N,U):
        raise ValueError(_("Invalid RDT value"))

    return _under_five_fever_uncomplicated(period, data_in)\
        .filter(encounter__ccreport__feverreport__rdt_result=value)\
        .count()

    
class UnderFiveFeverUncomplicatedRdtPositive(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_five_fever_uncomplicated_rdt_positive"
    short_name  = _("U5 Fv Uncompl RDT+")
    long_name   = _("Total number of danger signs reports "\
                    "for U5s with uncomplicated fever with "\
                    "a positive RDT result")

    @classmethod
    def _value(cls, period, data_in):
        return _under_five_fever_uncomplicated_rdt_value(period,\
            data_in, FeverReport.RDT_POSITIVE)

class UnderFiveFeverUncomplicatedRdtNegative(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_five_fever_uncomplicated_rdt_negative"
    short_name  = _("U5 Fv Uncompl RDT-")
    long_name   = _("Total number of danger signs reports "\
                    "for U5s with uncomplicated fever with "\
                    "a negative RDT result")

    @classmethod
    def _value(cls, period, data_in):
        return _under_five_fever_uncomplicated_rdt_value(period,\
            data_in, FeverReport.RDT_NEGATIVE)

def _under_five_fever_complicated(period, data_in):
    ds = DangerSignsReport\
        .objects\
        .filter(encounter__encounter_date__range=(period.start, period.end),\
            encounter__patient__in=data_in)\
        .annotate(n_signs=Count('danger_signs'))\
        .filter(danger_signs__code='FV')\
        .encounter_under_five()

    # Anyone with a fever and 3 or more danger signs has a
    # complicated fever
    d1 = ds\
        .filter(n_signs__gte=3)

    # Anyone with a fever and one other danger sign that is
    # NOT diarrhea has a complicated fever
    d2 = ds\
        .filter(n_signs=2)\
        .exclude(danger_signs__code='DR')

    return (d1|d2)


class UnderFiveFeverComplicated(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_five_fever_complicated"
    short_name  = _("U5 Fv Compl")
    long_name   = _("Total number of danger signs reports "\
                    "for U5s with complicated fever")

    @classmethod
    def _value(cls, period, data_in):
        return _under_five_fever_complicated(period, data_in).count()


class UnderFiveFeverComplicatedReferred(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_five_fever_complicated_referred"
    short_name  = _("U5 Fv Compl Ref")
    long_name   = _("Total number of danger signs reports "\
                    "for U5s with complicated fever where the "\
                    "patient was referred")

    @classmethod
    def _value(cls, period, data_in):
        return _under_five_fever_complicated(period, data_in)\
            .filter(encounter__ccreport__referralreport__urgency__isnull=False)\
            .count()

class UnderFiveFeverComplicatedReferredFollowUp(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "under_five_fever_complicated_referred_follow_up"
    short_name  = _("U5 Fv Compl Ref FU")
    long_name   = _("Total number of danger signs reports "\
                    "for U5s with complicated fever where the "\
                    "patient was referred and then had a follow-up "\
                    "visit between 18 and 72 hours after the referral")

    @classmethod
    def _value(cls, period, data_in):
        refs = _under_five_fever_complicated(period, data_in)\
            .filter(encounter__ccreport__referralreport__urgency__isnull=False)

        count = 0
        for r in refs:
            tstart = r.encounter.encounter_date + timedelta(seconds=60*60*18)
            tend = r.encounter.encounter_date + timedelta(seconds=60*60*72)

            f = FollowUpReport\
                .objects\
                .filter(encounter__patient=r.encounter.patient,\
                    encounter__encounter_date__gt=tstart,
                    encounter__encounter_date__lte=tend)
           
            if f.count():
                count += 1

        return count

