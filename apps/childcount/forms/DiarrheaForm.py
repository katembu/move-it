#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Fever Logic'''

from datetime import datetime, timedelta

from django.utils.translation import ugettext as _

from childcount.forms.CCForm import CCForm
from childcount.models.reports import DiarrheaReport
from childcount.forms.utils import MultipleChoiceField
from childcount.exceptions import ParseError


class DiarrheaForm(CCForm):
    KEYWORDS = {
        'en': ['d'],
    }
    '''
    home_field = MultipleChoiceField()
    home_field.add_choice('en', DiarrheaReport.HOME_YES, 'Y')
    home_field.add_choice('en', DiarrheaReport.HOME_NO, 'N')
    home_field.add_choice('en', DiarrheaReport.HOME_UNKNOWN, 'U')
    '''

    treatment_field = MultipleChoiceField()
    treatment_field.add_choice('en', DiarrheaReport.TREATMENT_ORS, 'R')
    treatment_field.add_choice('en', DiarrheaReport.TREATMENT_ZINC, 'Z')

    def process(self, patient):
        #self.home_field.set_language(self.message.reporter.language)
        self.treatment_field.set_language(self.message.reporter.language)
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info, expected %s (%s)") % \
                                (self.PREFIX, \
                                 '/'.join(self.treatment_field.valid_choices())))

        '''if not self.home_field.is_valid_choice(self.params[1]):
            raise ParseError(_(u"Eligible for home treatment must be "\
                               "%(choices)s") % \
                              {'choices': self.home_field.choices_string()})'''
        if not self.treatment_field.is_valid_choice(self.params[1]):
            raise ParseError(_(u"Treatment choices are "\
                               "%(choices)s") % \
                              {'choices': self.treatment_field.choices_string()})

        response = ""
        created_by = self.message.persistant_connection.reporter.chw

        #home_treatment = self.home_field.get_db_value(self.params[1])
        treatment = self.treatment_field.get_db_value(self.params[1])
        fr = DiarrheaReport(created_by=created_by,  \
                            patient=patient, treatment=treatment)
        #                     patient=patient, home_treatment=home_treatment)
        fr.save()
        
        if treatment == DiarrheaReport.TREATMENT_ORS:
            response += _("Treated with ORS")
        elif treatment == DiarrheaReport.TREATMENT_ZINC:
            response += _("Treated with Zinc")
        '''
        if home_treatment == DiarrheaReport.HOME_YES:
            response += _("Eligible for home treatment")
        else:
            response += _("Not Eligible for home treatment")
        '''

        return response
