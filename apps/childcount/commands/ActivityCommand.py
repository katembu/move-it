#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from datetime import datetime, timedelta

from django.utils.translation import ugettext as _

from childcount.models import CHW
from childcount.commands import CCCommand
from childcount.utils import authenticated

from childcount.indicators import nutrition
from childcount.indicators import household
from childcount.indicators import fever
from childcount.indicators import registration

from reportgen.timeperiods import Month

class ActivityCommand(CCCommand):

    KEYWORDS = {
        'en': ['activity'],
        'fr': ['activity'],
    }

    @authenticated
    def process(self):
        class LastSevenDays(object):
            end = datetime.today()
            start = end - timedelta(7)
    
        # Default to last seven days
        period = LastSevenDays

        if self.params.__len__() > 1:
            period_str = self.params[1]
            if period_str.lower() not in [_("week"), _("month")]:
                raise ValueError(_("Unknown period name: %s") % period_str)
    
            if period_str.lower() == _("month"):
                # Period is month
                if datetime.today().day < 10:
                    # Use last month if it's the start of this month
                    period = Month.periods()[1]
                else:
                    # Use this month otherwise
                    period = Month.periods()[0]

        chw = self.message.reporter.chw
        patients = chw.patient_set.all()

        p = {}
        p['sdate'] = period.start.strftime('%d %b')
        p['edate'] = period.end.strftime('%d %b')
        p['severemuac'] = nutrition.Sam(period, patients)
        p['numhvisit'] = household.Total(period, patients)
        p['muac'] = nutrition.Mam(period, patients)
        p['rdt'] = fever.Total(period, patients)
        p['household'] = registration.Household(period, patients)
        p['tclient'] = registration.Total(period, patients)
        p['ufive'] = registration.UnderFive(period, patients)
        p['unine'] = registration.UnderNineMonths(period, patients)
        p['underone'] = registration.UnderOne(period, patients)

        self.message.respond(_(u"(%(sdate)s->%(edate)s): " \
                                "%(numhvisit)d household visit, %(muac)d " \
                                "MUAC (%(severemuac)d SAM/MAM) %(rdt)d RDT." \
                                " You have %(household)d households" \
                                ", %(ufive)d under 5y, %(underone)d under "\
                                "1y, %(unine)d under 9m, "\
                                "%(tclient)d total" \
                                " registered clients") % p)
