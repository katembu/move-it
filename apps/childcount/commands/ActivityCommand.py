#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from django.utils.translation import ugettext as _

from reversion import revision
from reversion.models import Revision, Version
from childcount.models.ccreports import TheCHWReport

from childcount.commands import CCCommand
from childcount.utils import authenticated
from childcount.exceptions import Inapplicable


class ActivityCommand(CCCommand):

    KEYWORDS = {
        'en': ['activity'],
        'fr': ['activity'],
    }

    @authenticated
    def process(self):
        chw = self.message.reporter.chw
        thechw = TheCHWReport.objects.get(id=chw.id)
        period = "week"
        summary = None
        if self.params.__len__() > 1:
            period = self.params[1]

            if period == "month":
                today = datetime.today()
                # include last months summary if we are less than 10 days into
                # this month
                if today.day < 10:
                    start_date = today + relativedelta(months=-1, day=1, \
                                    hour=0, minute=0, second=0, microsecond=0)
                else:
                    start_date = today + relativedelta(day=1, \
                                    hour=0, minute=0, second=0, microsecond=0)
                summary = thechw.chw_activities_summary(start_date, today)
        if not summary:
            summary = thechw.activity_summary()
        self.message.respond(_(u"(%(sdate)s->%(edate)s): " \
                                "%(numhvisit)d household visit, %(muac)d " \
                                "MUAC(%(severemuac)d SAM/MAM) %(rdt)d RDT." \
                                " You have %(household)d households" \
                                ", %(ufive)d under five, %(underone)d under "\
                                "1y, %(unine)d under 9m,"\
                                "%(tclient)d total" \
                                " registerd clients") % summary)
