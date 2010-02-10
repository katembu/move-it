#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from datetime import datetime, timedelta
from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models import  Case
from childcount.models.reports import PregnancyReport


class MobileForm(CCForm):
    KEYWORDS = {
        'en': ['mobi'],
    }

    def process(self, patient):
        if len(self.params) < 2:
            return False
        response = ''
        created_by = self.message.persistent_connection.reporter.chw

        patient.mobile = self.params[1]
        patient.save()
        return response
