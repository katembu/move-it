#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re
import time
from datetime import date

from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.exceptions import BadValue, ParseError, InvalidDOB
from childcount.exceptions import Inapplicable
from childcount.models.reports import DeathReport
from childcount.models import Patient
from childcount.utils import DOBProcessor


class DeathForm(CCForm):
    KEYWORDS = {
        'en': ['dda'],
    }

    def process(self, patient):
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info, expected date of death"))

        if DeathReport.objects.filter(patient=patient).count() > 0:
            dr = DeathReport.objects.filter(patient=patient)[0]
            raise Inapplicable(_(u"A death report for %(p)s was already " \
                                  "submited by %(chw)s") % \
                                  {'p': patient, 'chw': dr.created_by})

        chw = self.message.persistant_connection.reporter.chw

        dod_str = ' '.join(self.params[1:])
        try:
            dod, variance = DOBProcessor.from_dob(chw.language, dod_str)
        except InvalidDOB:
            raise BadValue(_(u"Could not understand date of death: %(dod)s") %\
                             {'dod': dod_str})

        dr = DeathReport(created_by=chw, patient=patient, \
                         death_date=dod)
        dr.save()

        patient.status = Patient.STATUS_DEAD
        patient.save()

        self.response = _("Died on %(dod)s") % {'dod': dod}
