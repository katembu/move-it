#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models import CHW, Referral
from childcount.models.reports import HealthReport

from childcount.exceptions import ParseError, BadValue
from childcount.forms.utils import MultipleChoiceField


class HealthStatusForm(CCForm):
    KEYWORDS = {
        'en': ['h'],
    }
    visits_field = MultipleChoiceField()
    visits_field.add_choice('en', HealthReport.VISITED_CLINIC_YES, 'Y')
    visits_field.add_choice('en', HealthReport.VISITED_CLINIC_NO, 'N')
    visits_field.add_choice('en', HealthReport.VISITED_CLINIC_UNKOWN, 'U')
    visits_field.add_choice('en', HealthReport.VISITED_CLINIC_INPATIENT, 'K')
    
    signs_field = MultipleChoiceField()
    signs_field.add_choice('en', HealthReport.DANGER_SIGNS_PRESENT, 'S')
    signs_field.add_choice('en', HealthReport.DANGER_SIGNS_NONE, 'N')
    signs_field.add_choice('en', HealthReport.DANGER_SIGNS_UNKOWN, 'U')
    signs_field.add_choice('en', HealthReport.DANGER_SIGNS_UNAVAILABLE, 'W')
    
    def process(self, patient):
        keyword = self.params[0]
        self.visits_field.set_language(self.message.reporter.language)
        self.visits_field.set_language(self.message.reporter.language)
        
        if len(self.params) < 3:
            raise ParseError(_(u"Not enough info, expected (%s) (%s)") % \
                                ('/'.join(self.visits_field.valid_choices()), \
                                 '/'.join(self.signs_field.valid_choices())))

        
        if not self.visits_field.is_valid_choice(self.params[1]):
            raise ParseError(_(u"Clinic visits must be %(choices)s") % \
                              {'choices': self.visits_field.choices_string()})

        visits_db = self.visits_field.get_db_value(self.params[1])
        visits_user = self.visits_field.propper_answer(self.params[1])

        self.signs_field.set_language(self.message.reporter.language)

        if not self.signs_field.is_valid_choice(self.params[2]):
            raise ParseError(_(u"Danger signs must be %(choices)s") % \
                              {'choices': self.signs_field.choices_string()})

        signs_db = self.signs_field.get_db_value(self.params[2])
        signs_user = self.visits_field.propper_answer(self.params[2])
        
        
        created_by = self.message.persistant_connection.reporter.chw

        #TODO Create referral
        '''
        if danger_signs == HealthReport.DANGER_SIGNS_PRESENT:
            rf = Referral(created_by=created_by, patient=patient)
            rf.save()
            response = _('Danger signs present.')
        '''

        hr = HealthReport(created_by=created_by, patient=patient, \
                visited_clinic=visits_db, danger_signs=signs_db)
        hr.save()
        response = ""
        
        if visits_db == HealthReport.VISITED_CLINIC_YES:
            response += _(u"Did visit clinic")
        elif visits_db == HealthReport.VISITED_CLINIC_NO:
            response += _(u"Did not visit clinic")
        elif visits_db == HealthReport.VISITED_CLINIC_UNKOWN:
            response += _(u"Unkown clinic visit")
        elif visits_db == HealthReport.VISITED_CLINIC_INPATIENT:
            response += _(u"Currently inpatient")
            
        response += ", "
        
        if signs_db == HealthReport.DANGER_SIGNS_PRESENT:
            response += _(u"Danger signs present")
        elif signs_db == HealthReport.DANGER_SIGNS_NONE:
            response += _(u"No danger signs")
        elif signs_db == HealthReport.DANGER_SIGNS_UNKOWN:
            response += _(u"Unknown danger signs")
        elif signs_db == HealthReport.DANGER_SIGNS_UNAVAILABLE:
            response += _(u"Danger signs not available")

        return response
