
from django.utils.translation import ugettext as _

from indicator import Indicator
from indicator import QuerySetType

from childcount.models import Patient
from childcount.models.reports import MedicineGivenReport

NAME = _("Medicine Given")

def _medicine_given(period, data_in, drug_code):
    return MedicineGivenReport\
        .objects\
        .filter(encounter__patient__in=data_in,\
            encounter__encounter_date__range=(period.start, period.end),
            medicines__code=drug_code)\
        .count()

class Ors(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "ors"
    short_name  = _("ORS")
    long_name   = _("Number of ORS doses distributed")

    @classmethod
    def _value(cls, period, data_in):
        return _medicine_given(period, data_in, 'R')

class Antimalarial(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "antimalarial"
    short_name  = _("Antimalarial")
    long_name   = _("Number of antimalarial doses distributed")

    @classmethod
    def _value(cls, period, data_in):
        return _medicine_given(period, data_in, 'ACT')

