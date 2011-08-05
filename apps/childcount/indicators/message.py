
from datetime import timedelta

from django.utils.translation import ugettext as _

from indicator import Indicator
from indicator import IndicatorPercentage
from indicator import IndicatorDifference
from indicator import QuerySetType

from reporters.models import Reporter
from logger_ng.models import LoggedMessage

NAME = _("Message")

class Total(Indicator):
    type_in     = QuerySetType(Reporter)
    type_out    = int

    slug        = "total"
    short_name  = _("# Msg")
    long_name   = _("Total number of messages sent to server")

    @classmethod
    def _value(cls, period, data_in):
        return LoggedMessage\
            .objects\
            .filter(reporter__in=data_in,\
                direction=LoggedMessage.DIRECTION_INCOMING,
                date__range=(period.start, period.end))\
            .count()

class Sms(Indicator):
    type_in     = QuerySetType(Reporter)
    type_out    = int

    slug        = "sms"
    short_name  = _("# SMS")
    long_name   = _("Total number of SMS messages sent to server")

    @classmethod
    def _value(cls, period, data_in):
        return LoggedMessage\
            .objects\
            .filter(reporter__in=data_in,\
                direction=LoggedMessage.DIRECTION_INCOMING,
                backend="pygsm",
                date__range=(period.start, period.end))\
            .count()

class Error(Indicator):
    type_in     = QuerySetType(Reporter)
    type_out    = int

    slug        = "error"
    short_name  = _("# Err")
    long_name   = _("Total number of error messages sent from server")

    @classmethod
    def _value(cls, period, data_in):
        return LoggedMessage\
            .objects\
            .filter(reporter__in=data_in,\
                direction=LoggedMessage.DIRECTION_OUTGOING,
                date__range=(period.start, period.end),\
                text__icontains=_("error"))\
            .count()

class ErrorPerc(IndicatorPercentage):
    type_in     = QuerySetType(Reporter)

    slug        = "error_perc"
    short_name  = _("% Err")
    long_name   = _("Percentage of messages from server that indicate "\
                    "an error")

    cls_num     = Error
    cls_den     = Total

def _timedelta_to_days(diff):
    seconds = diff.seconds / float(24 * 60 * 60)
    mseconds = diff.microseconds / 1000000.0

    # Convert timedelta into a float of days 
    return float(diff.days) + seconds + mseconds

class PerDay(Indicator):
    type_in     = QuerySetType(Reporter)
    type_out    = float

    slug        = "per_day"
    short_name  = _("Per day")
    long_name   = _("Average number of messages received from "\
                    "the reporter set per day")

    @classmethod
    def _value(cls, period, data_in):
        # Get length of period
        days = _timedelta_to_days(period.end - period.start)
        
        if days <= 0: 
            return float('inf')

        # Get number of msgs received
        total = Total(period, data_in)

        return (total/days)

class DaysSinceSent(Indicator):
    type_in     = QuerySetType(Reporter)
    type_out    = float

    slug        = "days_since_sent"
    short_name  = _("Days since")
    long_name   = _("Number of days since the server received a message "\
                    "from a user in the input set")

    @classmethod
    def _value(cls, period, data_in):
        try:
            latest = LoggedMessage\
                .objects\
                .filter(reporter__in=data_in,\
                    direction=LoggedMessage.DIRECTION_INCOMING,
                    date__range=(period.start, period.end))\
                .latest('date')
        except LoggedMessage.DoesNotExist:
            return float('inf')

        return _timedelta_to_days(period.end - latest.date)

