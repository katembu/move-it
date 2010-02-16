#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Child logic
'''

from django.utils.translation import ugettext as _

from childcount.forms import CCForm, FeverForm
from childcount.models.reports import NewbornReport, ChildReport, NeonatalReport
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
        self.breast_field.set_language(self.message.reporter.language)
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
            clinic_vists = '' + self.params[2]
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


class ChildForm(CCForm):
    KEYWORDS = {
        'en': ['c'],
    }
    fever = None
    fever_field = MultipleChoiceField()
    fever_field.add_choice('en', ChildReport.FEVER_YES, 'F')
    fever_field.add_choice('en', ChildReport.FEVER_NO, 'N')
    fever_field.add_choice('en', ChildReport.FEVER_UNKOWN, 'U')

    diarrhea_field = MultipleChoiceField()
    diarrhea_field.add_choice('en', ChildReport.DIARRHEA_YES, 'D')
    diarrhea_field.add_choice('en', ChildReport.DIARRHEA_NO, 'N')
    diarrhea_field.add_choice('en', ChildReport.DIARRHEA_UNKOWN, 'U')

    def process(self, patient):
        self.fever_field.set_language(self.message.reporter.language)
        self.diarrhea_field.set_language(self.message.reporter.language)
        if len(self.params) < 3:
            raise ParseError(_(u"Not enough info, expected (%s) (%s)") % \
                             (('/'.join(self.fever_field.valid_choices())),
                              ('/'.join(self.diarrhea_field.valid_choices()))))

        days, weeks, months = patient.age_in_days_weeks_months()
        created_by = self.message.persistant_connection.reporter.chw
        response = ''

        if months < 6:
            raise Inapplicable(_('Child is an Infant. Please fill out Newborn'\
                         ' form'))
        elif months > 59:
            raise Inapplicable(_('Child is older then 59 months.'))
        else:
            if not self.fever_field.is_valid_choice(self.params[1]):
                raise ParseError(_(u"Fever choices must be %(choices)s") % \
                              {'choices': self.fever_field.choices_string()})
            if not self.diarrhea_field.is_valid_choice(self.params[2]):
                raise ParseError(_(u"Diarrhea choices must be %(choices)s") % \
                            {'choices': self.diarrhea_field.choices_string()})

            self.fever = self.fever_field.get_db_value(self.params[1])
            if self.fever == ChildReport.FEVER_YES:
                response = _('Has fever')
            elif self.fever == ChildReport.FEVER_NO:
                response = _('No fever')
            else:
                response = _('Fever status unknown')

            response += ', '
            diarrhea = self.diarrhea_field.get_db_value(self.params[2])
            if diarrhea == ChildReport.DIARRHEA_YES:
                response += _('has diarrhea')
            elif diarrhea == ChildReport.DIARRHEA_NO:
                response += _('has no diarrhea')
            else:
                response += _('diarrhea status unknown')

            '''if diarrhea.upper() == 'D' and not diarrhea_form:
                response += _('Please treat child for diarrhea with ORS '\
                'and Zinc and record with ORS (+S) form')'''
            cr = ChildReport(created_by=created_by, patient=patient, \
                               fever=self.fever, diarrhea=diarrhea)
            cr.save()

        return response

    def post_process(self, message, forms_list):
        response = ''
        if self.fever == ChildReport.FEVER_YES and FeverForm not in forms_list:
            response = _('Please check child for malaria and shortness of '\
                             'breath using the fever (F+) Form.')
        return response


class NeonatalForm(CCForm):
    KEYWORDS = {
        'en': ['b'],
    }
    
    def process(self, patient):
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info, expected +%(command)s no. "\
                               "of clinic visits since delivery") % \
                               {'command': self.params[0].upper()})

        clinic_visits = '' + self.params[1]
        if not clinic_visits.isdigit():
            raise ParseError(_('Expected number of clinic visits since '\
                               'delivery'))

        days, weeks, months = patient.age_in_days_weeks_months()
 
        if days > 28:
            raise Inapplicable(_(u"The child is too old for this report"))
        
        clinic_visits = int(clinic_visits)
        created_by = self.message.persistant_connection.reporter.chw

        pr = NeonatalReport(created_by=created_by, patient=patient, \
                             clinic_visits=clinic_visits)
        pr.save()

        response = _('%(clinic_visits)s clinic visits') \
                    % {'clinic_visits': clinic_visits}
        return response
