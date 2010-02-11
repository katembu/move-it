#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Child logic
'''

from django.utils.translation import ugettext as _

from childcount.forms import CCForm, FeverForm
from childcount.models.reports import NewbornReport, ChildReport
from childcount.exceptions import Inapplicable, ParseError
from childcount.forms.utils import MultipleChoiceField


class NewbornForm(CCForm):
    KEYWORDS = {
        'en': ['n'],
    }

    breast_field = MultipleChoiceField()
    breast_field.add_choice('en', NewbornReport.BREAST_YES, 'Y')
    breast_field.add_choice('en', NewbornReport.BREAST_NO, 'N')
    breast_field.add_choice('en', NewbornReport.BREAST_UNKOWN, 'U')

    def process(self, patient):
        if len(self.params) < 3:
            raise ParseError(_(u"Not enough info, expected (no. of clinic "\
                               "visits) (%s)") % \
                                ('/'.join(self.breast_field.valid_choices())))
        
        days, weeks, months = patient.age_in_days_weeks_months()
        response = ''
        created_by = self.message.persistant_connection.reporter.chw

        if months >= 6 and months < 60:
            raise Inapplicable(_('Child is %(months)d months old. Please fill'\
                                 ' out CHILD (+C) form') % {'months': months})
        elif months > 59:
            raise Inapplicable(_('Child is older then 59 months.'))
        else:
            clinic_vists = ''+self.params[2]
            if not clinic_vists.isdigit():
                raise ParseError(_('Expected Number of clinic visits'))
            clinic_vists = int(clinic_vists)
            response = _('%(visits)s clinic visits') % {'visits': clinic_vists}
            if not self.breast_field.is_valid_choice(self.params[1]):
                raise ParseError(_('Breast feeding options are %(choices)s') \
                                 % {'choices': \
                                    self.breast_field.choices_string()})
            breast_only = self.breast_field.get_db_value(self.params[1])

            nr = NewbornReport(created_by=created_by, patient=patient, \
                            clinic_vists=clinic_vists, breast_only=breast_only)
            nr.save()

            response += ', '

            if breast_only == NewbornReport.BREAST_YES:
                response += _('is breast feeding only')
            elif breast_only == NewbornReport.BREAST_NO:
                response += _('is not breast feeding only')
            elif breast_only == NewbornReport.BREAST_UNKOWN:
                response += _('breast feeding only status unkown')
        return response


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
