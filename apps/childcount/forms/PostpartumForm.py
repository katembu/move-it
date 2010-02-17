#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from datetime import datetime, timedelta
from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models import  Case
from childcount.models.reports import PostpartumReport
from childcount.exceptions import ParseError,Inapplicable


class PostpartumForm(CCForm):
    KEYWORDS = {
        'en': ['a'],
    }

    def process(self, patient):
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info, expected (no. of clinic "\
                               "visits since delivery)"))

        clinic_visits = '' + self.params[1]
        if not clinic_visits.isdigit():
            raise ParseError(_('Expected number of clinic visits since '\
                               'delivery'))
        
        days, weeks, months = patient.age_in_days_weeks_months()

        #the mother should at least be 10 years
        if months/12 < 10:
            raise Inapplicable(_(u"The child is too young for this report"))

        clinic_visits = int(clinic_visits)
        created_by = self.message.persistant_connection.reporter.chw

        pr = PostpartumReport(created_by=created_by, patient=patient, \
                             clinic_visits=clinic_visits)
        pr.save()

        response = _('%(clinic_visits)s clinic visits') \
                    % {'clinic_visits': clinic_visits}
        return response
