#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re

from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.utils.translation import ugettext as _
from django.db.models import Count

from checksum import checksum

from reporters.models import Reporter
from locations.models import Location
from childcount.models import HealthId

from childcount.commands import CCCommand
from childcount.models import Patient
from childcount.models.PolioCampaignReport import PolioCampaignReport
from childcount.utils import authenticated, send_msg


class PolioSummaryCommand(CCCommand):

    KEYWORDS = {
        'en': ['plsummary'],
        'fr': ['plsummary'],
    }

    @authenticated
    def process(self):
        chw = self.message.persistant_connection.reporter.chw

        if PolioCampaignReport.objects.filter(chw=chw):
            rpts = PolioCampaignReport.objects.filter(patient__chw=chw)
            count = rpts.count()
            dob = datetime.today() + relativedelta(months=-59)
            underfive = Patient.objects.filter(chw=chw, dob__gte=dob,
                                        status=Patient.STATUS_ACTIVE)
            total = underfive.count()
            percentage = 0
            if total:
                percentage = round((count/float(total))*100, 2)
            resp = _(u"Vaccinated: %(count)s of %(total)s - %(percentage)s%%" \
                    % {'count': count, 'total': total,
                        'percentage': percentage})
            self.message.respond(resp)
            return True
        dob = datetime.today() + relativedelta(months=-59)
        underfive = Patient.objects.filter(dob__gte=dob,
                                    status=Patient.STATUS_ACTIVE)
        rpts = PolioCampaignReport.objects.filter()
        percentage = round((rpts.count()/float(underfive.count()))*100, 2)
        resp = _(u"%(percentage)s%% coverage, Total Reports: %(total)s. " % \
                {'total': rpts.count(), 'percentage': percentage})
        rpts = rpts.values('chw__location__name').annotate(Count('chw'))
        for loc in rpts:
            resp += u"%s: %s. " % (loc['chw__location__name'], loc['chw__count'])
        self.message.respond(resp)
        if self.params.__len__() > 1 and self.params[1] == 'all':
            for chw in CHW.objects.all():
                try:
                    send_msg(chw, resp)
                except:
                    pass
        return True
