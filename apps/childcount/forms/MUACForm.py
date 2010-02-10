#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re

from CCForm import CCForm
from childcount.models.reports import MUACReport

class MUACForm(CCForm):
    KEYWORDS = {
        'en': ['muac'],
    }

    def process(self, message, patient, params):
        print "Processing"

        if True or reporter.lang == 'en': 
            OEDEMA_CHOICES = {
                'y': MUACReport.OEDEMA_YES,
                'n': MUACReport.OEDEMA_NO,
                'u': MUACReport.OEDEMA_UNKOWN
            }

        regex = r'(?P<muac>\d+) +(?P<oedema>[a-z])?'

        match = re.match(regex, '23 g')
        gdict = match.groupdict()

        try:
            oedema = OEDEMA_CHOICES[gdict['oedema']]
        except KeyError:
            print "Oedema must be reported as %s (Yes), %s (No), or %s (Unknown)" % ('d','d','d')

        return True
