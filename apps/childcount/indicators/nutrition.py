
from django.utils.translation import ugettext as _

from indicator import Indicator
from indicator import IndicatorPercentage
from indicator import Percentage
from indicator import QuerySetType

from childcount.models.reports import NutritionReport
'''
class Total(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "total"
    short_name  = _("Total")
    long_name   = _("Number of neonatal reports")

    @classmethod
    def _value(cls, period, data_in):
        return NeonatalReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                encounter__encounter_date__range=(period.start, period.end))\
            .count()
'''              
