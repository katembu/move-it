
from django.db.models.aggregates import Count

from django.utils.translation import ugettext as _

from indicator import Indicator
from indicator import QuerySetType

from childcount.models import Patient
from childcount.models.reports import DangerSignsReport

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
            .encounter_under_five()\
            .annotate(n_signs=Count('danger_signs'))\
            .filter(danger_signs__code='DR', n_signs=1)

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

