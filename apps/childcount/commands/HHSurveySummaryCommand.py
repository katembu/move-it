#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from datetime import datetime, timedelta

from django.utils.translation import ugettext as _

from reversion import revision
from reversion.models import Revision, Version
from childcount.models.ccreports import TheBHSurveyReport

from childcount.commands import CCCommand
from childcount.utils import authenticated
from childcount.utils import send_msg
from childcount.exceptions import Inapplicable


class HHSurveySummaryCommand(CCCommand):

    KEYWORDS = {
        'en': ['bsummary'],
        'fr': ['bsummary'],
    }

    @authenticated
    def process(self):
        chw = self.message.persistant_connection.reporter.chw

        thechw = TheBHSurveyReport.objects.get(id=chw.id)
        summary = thechw.bednet_aggregates()
        summary.update({'number_not_surveyed': \
                thechw.number_of_households - summary['encounter__count']})
        self.message.respond(_(u"# HHs covered: %(encounter__count)s, "\
                            "#SS: %(sleeping_sites__sum)s, "\
                            "#functioningN: %(function_nets__sum)s, "\
                            "#damagedN: %(damaged_nets__sum)s, "\
                            "#earlierN: %(earlier_nets__sum)s, "\
                            "#+BU: %(bednet_util__count)s, "\
                            "#+DW: %(drinking_water__count)s, #+SAN: "\
                            "%(sanitation__count)s. #HHs NOT covered: "\
                            "%(number_not_surveyed)s") % \
                            summary)
        not_surveyed = thechw.households_not_surveyed()
        msg = _(u"HHs NOT Covered")
        for i in range((not_surveyed.count() / 15) + 1):
            hhs = u', ' . join([h.health_id.upper() \
                                for h in not_surveyed[15 * i:15 * (i + 1)]])
            send_msg(chw, u"%s: %s" % (msg, hhs))
