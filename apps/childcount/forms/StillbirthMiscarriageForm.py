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
from childcount.models.reports import StillbirthMiscarriageReport
from childcount.utils import DOBProcessor


class StillbirthMiscarriageForm(CCForm):
    KEYWORDS = {
        'en': ['sbm'],
    }

    def process(self, patient):
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info, expected date of " \
                                "stillbirth or miscarriage"))

        chw = self.message.persistant_connection.reporter.chw

        doi_str = ' '.join(self.params[1:])
        try:
            doi, variance = DOBProcessor.from_dob(chw.language, doi_str)
        except InvalidDOB:
            raise BadValue(_(u"Could not understand date: %(dod)s") %\
                             {'dod': doi_str})

        sbmr = StillbirthMiscarriageReport(created_by=chw, patient=patient, \
                         incident_date=doi)
        sbmr.save()

        self.response = _("Stillbirth or miscarriage on %(doi)s") % \
                         {'doi': doi}
