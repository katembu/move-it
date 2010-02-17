#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from datetime import datetime, timedelta
from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models import  Case
from childcount.models.reports import PregnancyReport
from childcount.exceptions import ParseError
from childcount.forms.utils import MultipleChoiceField


class PregnancyForm(CCForm):
    KEYWORDS = {
        'en': ['p'],
    }

    def process(self, patient):
        if len(self.params) < 3:
            raise ParseError(_(u"Not enough info, expected (month of "\
                               "pregnancy[1-9]) (no. of anc visits)") % \
                                ('/'.join(self.fever_field.valid_choices())))

        clinic_visits = unicode(self.params[2])
        if not clinic_visits.isdigit():
            raise ParseError(_('No. of ANC visits, expects a number.'))
        clinic_visits = int(clinic_visits)
        month = unicode(self.params[1])
        if not month.isdigit():
            raise ParseError(_('Month of pregnancy, expects a number '\
                               'between 1-9'))
        month = int(month)
        created_by = self.message.persistant_connection.reporter.chw
        response = ''

        pcases = Case.objects.filter(patient=patient, \
                                     type=Case.TYPE_PREGNANCY, \
                                     status=Case.STATUS_OPEN)

        if pcases.count() == 0:
            #create a new pregnancy case
            now = datetime.now()
            #expected birth date
            expires_on = now - timedelta(int((9 - month) * 30.4375))
            case = Case(patient=patient, type=Case.TYPE_PREGNANCY, \
                 expires_on=expires_on)
            case.save()
        else:
            case = pcases.latest()
        #TODO give this feedback
        if month == 2 and clinic_visits < 1 \
            or month == 5 and clinic_visits < 2 \
            or month == 7 and clinic_visits < 3 \
            or month == 8 and clinic_visits < 8:
            response += _('Remind the woman she is due for a clinic visit')

        pr = PregnancyReport(created_by=created_by, patient=patient, \
                             pregnancy_month=month, \
                             clinic_visits=clinic_visits)
        pr.save()

        response = _('%(clinic_visits)s clinic visits, month %(month)s') \
                    % {'clinic_visits': clinic_visits, 'month': month}
        return response
