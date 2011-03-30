from django.utils.translation import ugettext as _

from reportgen.timeperiods.PeriodType import PeriodType
from reportgen.timeperiods.Period import Period
from reportgen.timeperiods.SubPeriod import SubPeriod

from reportgen.timeperiods.definitions.FourWeeks import FourWeeks
from reportgen.timeperiods.definitions.Month import Month

PERIOD_TYPES = [FourWeeks, Month]
PERIOD_CHOICES = [(pt.code, "%s (0-%d)" % (pt.title, pt.n_periods-1)) \
                            for pt in PERIOD_TYPES]

