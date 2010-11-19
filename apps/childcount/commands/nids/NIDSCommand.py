#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re

from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.utils.translation import ugettext as _

from checksum import checksum

from reporters.models import Reporter
from locations.models import Location
from childcount.models import HealthId

from childcount.commands import CCCommand
from childcount.models import Patient
from childcount.models.PolioCampaignReport import PolioCampaignReport
from childcount.utils import authenticated


class NIDSCommand(CCCommand):

    KEYWORDS = {
        'en': ['nids', 'n1ds', 'nid', 'n1d', 'polio', 'p0l10'],
        'fr': ['nids'],
    }

    @authenticated
    def process(self):
        chw = self.message.persistant_connection.reporter.chw

        if self.params.__len__() < 2:
            self.message.respond(_(u"Command requires atleast one health id"), \
                                   'error')
            return True
        health_ids = self.params[1:]
        patients = []
        invalid_hids = []
        over_age = []
        for health_id in health_ids:
            try:
                patient = Patient.objects.get(health_id__iexact=health_id)
            except Patient.DoesNotExist:
                invalid_hids.append(health_id)
            else:
                fm = datetime.now().date() + relativedelta(months=-59)
                if patient.dob < fm:
                    over_age.append(patient)
                else:
                    patients.append(patient)
        reported = []
        successful = []
        for patient in patients:
            try:
                rpt = PolioCampaignReport.objects.get(patient=patient)
            except PolioCampaignReport.DoesNotExist:
                rpt = PolioCampaignReport(patient=patient, chw=chw)
                rpt.save()
                successful.append(patient)
            else:
                reported.append(patient)
        resp = u''
        if successful.__len__():
            if successful.__len__() > 5:
                tmp = ', '.join([p.health_id.upper() for p in successful])
            else:
                tmp = ', '.join(["%s" % p for p in successful])
            resp += _(u"Successful: %(patients)s. " % {'patients': tmp})
        if over_age.__len__():
            resp += _(u"Over 59m: %(patients)s. " % {'patients':
                ', '.join([p.health_id.upper() for p in over_age])})
        if invalid_hids.__len__():
            resp += _(u"Invalid HealthID: %(hid)s. " % {'hid':
                                            ','. join(invalid_hids)})
        if reported.__len__():
            resp += _(u"Already reported: %(patients)s. " % {'patients':
                ', '.join([p.health_id.upper() for p in reported])})
        self.message.respond(resp)
        return True
