#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin
import re

from django.utils.translation import ugettext as _

from CCForm import CCForm
from childcount.models.reports import MUACReport
from childcount.exceptions import ParseError, BadValue, Inapplicable
from childcount.forms.utils import MultipleChoiceField


class MUACForm(CCForm):
    KEYWORDS = {
        'en': ['m', 'muac'],
    }

    WEIGHT = 'kg'

    oedema_field = MultipleChoiceField()
    oedema_field.add_choice('en', MUACReport.OEDEMA_YES, 'Y')
    oedema_field.add_choice('en', MUACReport.OEDEMA_NO, 'N')
    oedema_field.add_choice('en', MUACReport.OEDEMA_UNKOWN, 'U')


    def process(self, patient):
        response = ""
        keyword = self.params[0]
        
        days, weeks, months = patient.age_in_days_weeks_months()

        if days <= 30:
            raise Inapplicable(_(u"Child is too young for MUAC"))
        elif months > 59:
            raise Inapplicable(_(u"Child is older then 59 months. For any " \
                                  "concerns about child please refer to " \
                                  "a clinic."))


        if len(self.params) < 3:
            raise ParseError(_(u"Not enough info, expected muac, oedema"))

        if not self.params[1].isdigit():
            raise ParseError(_(u"MUAC must be a number"))

        muac = int(self.params[1])
        if muac < 50:
            raise BadValue(_('MUAC too low. If correct, refer child ' \
                             'IMMEDIATELY!'))
        elif muac > 250:
            raise BadValue(_('MUAC too high. Correct and resend.'))

        self.oedema_field.set_language(self.message.reporter.language)

        if not self.oedema_field.is_valid_choice(self.params[2]):
            raise ParseError(_(u"Oedema must be " \
                                "%(choices)s") % \
                               {'choices': self.oedema_field.choices_string()})

        oedema_db = self.oedema_field.get_db_value(self.params[2])
        oedema_user = self.oedema_field.propper_answer(self.params[2])

        created_by = self.message.persistant_connection.reporter.chw

        mr = MUACReport(created_by=created_by, oedema=oedema_db, \
                                muac=muac, patient=patient)
        mr.save()

        response = _('%(muac)s, Oedema:%(oedema)s') % \
                   {'muac': mr.muac, 'oedema': oedema_user}
        if len(self.params) > 3:
            try:
                weight = float(re.match(r'([0-9]*\.[0-9]+|[0-9]+)(' + \
                                        self.WEIGHT + ')?', self.params[3], \
                                        re.IGNORECASE).groups()[0])

                mr.weight = weight
                mr.save()
                response += _(", %(weight)s%(prefix)s") % {'weight': weight, \
                                                        'prefix': self.WEIGHT}
            except:
                response += _('Unknown value for weight %s') % self.params[3]

        #TODO Referral / Case
        '''
        if mr.status == MUACReport.STATUS_SEVERE:
            info = {}
            info.update({'last_name': patient.last_name,
                         'first_name': patient.first_name,
                         'age': patient.age(),
                         'zone': patient.zone})
            rf = Referral(patient=patient)
            info.update({'refid': rf.referral_id})

            expires_on = datetime.now() + timedelta(15)
            case = Case(patient=patient, expires_on=expires_on)
            case.save()

            response = _('SAM> Last, First (AGE) LOCATION has acute '\
                     'malnutrition. Please refer child to clinic '\
                     'IMMEDIATELY. (%(refid)s')
            #setup alert
            # SAM> Last, First (AGE), LOCATION has SAM. CHW NAME -
            #CHWMOBILE. (REFID)
        '''

        return response
        
