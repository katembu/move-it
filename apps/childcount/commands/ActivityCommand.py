#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from datetime import datetime, timedelta

from django.utils.translation import ugettext as _

from childcount.models import CHW,  Patient
from childcount.commands import CCCommand
from childcount.utils import authenticated
from reportgen.timeperiods import TwelveMonths

class LastSevenDays(object):
    end = datetime.today()
    start = end - timedelta(7)

class ActivityCommand(CCCommand):

    KEYWORDS = {
        'en': ['activity'],
    }

    WEEK = {
        'en': 'week',
    }

    MONTH = {
        'en': 'month',
    }
    
    MONTHS = {
        'en': {
            'jan': 0,
            'feb': 1,
            'mar': 2,
            'apr': 3,
            'may': 4,
            'jun': 5,
            'jul': 6,
            'aug': 7,
            'sep': 8,
            'oct': 9,
            'nov': 10,
            'dec': 11,
        },
    }

    def _locale_keyword(self, lot):
        # Get month abbreviations in locale,
        # defaulting to English
        lang = self.message.reporter.language

        if lang in lot:
            return lot[lang]
        else:
            return lot['en']

    def _parse_period(self, keyword):

        keyword = keyword.lower()
        month_names = {}

        key_abbrs = self._locale_keyword(self.MONTHS)
        key_month = self._locale_keyword(self.MONTH)
        key_week = self._locale_keyword(self.WEEK)

        valid_periods = [key_week, key_month] + key_abbrs.keys()
        months = TwelveMonths.periods()[0].sub_periods()

        if keyword == key_month:
            # Use last month if it's the start of this month
            return months[10] if datetime.today().day < 10 else months[11]

        elif keyword == key_week:
            return LastSevenDays

        elif keyword in key_abbrs:
            # is 0 if user submitted "jan", 1 if "feb", ...
            index = key_abbrs[keyword]

            # is 1 if today is in January, 2, if in Feb, ...
            this_month = months[11].start.month

            shifted_index = (index - this_month) % 12
            return months[shifted_index]

        else:
            raise ValueError(_("Unknown period name: %(name)s. "\
                                "Valid periods are %(valid)s.") % \
                                {'name': keyword,
                                'valid': ', '.join(valid_periods)})


    @authenticated
    def process(self):
        chw = self.message.reporter.chw

        allowed_groups = ("registrar")
        reporters = CHW.objects.filter(user_ptr__groups__name__in=allowed_groups)
        '''
        if chw not in reporters:
            raise ParseError(_(u"Youre not allowed to report Events "))

        if len(self.params) == 1:
            # Default to last seven days
            period = LastSevenDays

        elif len(self.params) == 2:
            period = self._parse_period(self.params[1].lower())

        else:
            self.message.respond(_(u"Use ACTIVITY followed by WEEK, MONTH, or "\
                                    "the 3-letter month code."))
            return True
        '''   

        p = {}     
        p['totalbirth'] = Patient.objects.filter(event_type = Patient.BIRTH).count()
        p['tbirth'] = Patient.objects.filter(event_type = Patient.BIRTH, cert_status = Patient.CERT_UNVERIFIED).count()
        p['death'] = Patient.objects.filter(event_type = Patient.DEATH).count()
        p['tdeath'] = Patient.objects.filter(event_type = Patient.DEATH,cert_status = Patient.CERT_UNVERIFIED).count()

        self.message.respond(_(u"(%(totalbirth)d Total Birth, %(tbirth)d " \
                                "Unverified Birth." \
                                "%(death)d Total Death" \
                                ", %(tdeath)d Unverified Death") % p)
