'''
AppointmentReport
'''

from django.utils.translation import ugettext as _

from indicator import Indicator
from indicator import IndicatorPercentage
from indicator import QuerySetType

from childcount.models import Patient
from childcount.models.reports import AppointmentReport

NAME = _("Appointment")

class Total(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "total"
    short_name  = _("Appointments")
    long_name   = _("Total number of appointment this period")

    @classmethod
    def _value(cls, period, data_in):
        return AppointmentReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                appointment_date__range=(period.start, period.end))\
            .count()

class Reminded(Indicator):
    type_in     = QuerySetType(Patient)
    type_out    = int

    slug        = "reminded"
    short_name  = _("Appt. Reminded")
    long_name   = _("Total number of appointments reminded this period")

    @classmethod
    def _value(cls, period, data_in):
        return AppointmentReport\
            .objects\
            .filter(encounter__patient__in=data_in,\
                appointment_date__range=(period.start, period.end),\
                status__in=(AppointmentReport.STATUS_CLOSED, \
                                AppointmentReport.STATUS_PENDING_CV))\
            .count()

class RemindedPerc(IndicatorPercentage):
    type_in     = QuerySetType(Patient)

    slug        = "reminded_perc"
    short_name  = _("% Appt. Reminded")
    long_name   = _("Percentage of appointments reminded this period")

    cls_num     = Reminded
    cls_den     = Total

