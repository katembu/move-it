#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Child logic
'''

from django.utils.translation import ugettext_lazy as _

from childcount.forms import CCForm, FeverForm
from childcount.models import CHW
from childcount.models.reports import NewbornReport, ChildReport


class NewbornForm(CCForm):
    KEYWORDS = {
        'en': ['n'],
    }

    def process(self, patient):
        if len(self.params) < 3:
            return False
        clinic_vists = self.params[2]
        breast_only = self.params[1]
        days, months = patient.age_in_days_months()
        response = ''
        created_by = self.message.persistent_connection.reporter.chw

        if months >= 6 and months < 60:
            response = _('Child is %(months)d months old. Please fill out '\
                         'CHILD (+C) form') % {'months': months}
        elif months > 59:
            response = _('Child is older then 59 months.')
        else:
            nr = NewbornReport(created_by=created_by, patient=patient, \
                            clinic_vists=clinic_vists, breast_only=breast_only)
            nr.save()

        return True


class CHildForm(CCForm):
    KEYWORDS = {
        'en': ['c'],
    }
    fever = None

    def process(self, patient):
        if len(self.params) < 3:
            return False
        fever = self.params[1]
        diarrhea = self.params[2]
        days, months = patient.age_in_days_months()
        created_by = self.message.persistent_connection.reporter.chw
        response = ''

        if months < 6:
            response = _('Child is an Infant. Please fill out Newborn ' \
                         '(+N) form')
        elif months > 59:
            response = _('Child is older then 59 months.')
        else:
            if fever.upper() == ChildReport.FEVER_YES:
                self.fever = ChildReport.FEVER_YES
            '''if diarrhea.upper() == 'D' and not diarrhea_form:
                response += _('Please treat child for diarrhea with ORS '\
                'and Zinc and record with ORS (+S) form')'''
            cr = ChildReport(created_by=created_by, patient=patient, \
                               fever=fever, diarrhea=diarrhea)
            cr.save()

        return True

    def post_process(self, message, forms_list):
        if self.fever == ChildReport.FEVER_YES and FeverForm not in forms_list:
            response = _('Please check child for malaria and shortness of '\
                             'breath using the fever (F+) Form.')
