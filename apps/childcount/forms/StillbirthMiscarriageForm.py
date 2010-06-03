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
from childcount.models import Encounter
from childcount.models.reports import StillbirthMiscarriageReport
from childcount.utils import DOBProcessor


class StillbirthMiscarriageForm(CCForm):
    KEYWORDS = {
        'en': ['sbm'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_PATIENT

    def process(self, patient):
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info. Expected: Date of " \
                                "stillbirth or miscarriage."))

        try:
            sbmr = StillbirthMiscarriageReport.objects.get(\
                                                    encounter=self.encounter)
            sbmr.reset()
        except StillbirthMiscarriageReport.DoesNotExist:
            sbmr = StillbirthMiscarriageReport(encounter=self.encounter)
        sbmr.form_group = self.form_group

        doi_str = ' '.join(self.params[1:])
        try:
            doi, variance = DOBProcessor.from_dob(self.chw.language, doi_str)
        except InvalidDOB:
            raise BadValue(_(u"Could not understand date: %(dod)s.") %\
                             {'dod': doi_str})

        sbmr.incident_date = doi
        sbmr.save()

        self.response = _("Stillbirth or miscarriage on %(doi)s.") % \
                         {'doi': doi}
