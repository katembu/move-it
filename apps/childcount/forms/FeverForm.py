#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Fever Logic'''

from datetime import datetime, timedelta

from django.utils.translation import ugettext as _

from childcount.forms.CCForm import CCForm
from childcount.models import Case
from childcount.models.reports import FeverReport
from childcount.models.shared_fields import RDTField
from childcount.forms.utils import MultipleChoiceField
from childcount.exceptions import ParseError, Inapplicable


class FeverForm(CCForm):
    KEYWORDS = {
        'en': ['f'],
    }
    rdt_field = MultipleChoiceField()
    rdt_field.add_choice('en', RDTField.RDT_POSITIVE, 'Y')
    rdt_field.add_choice('en', RDTField.RDT_NEGATIVE, 'N')
    rdt_field.add_choice('en', RDTField.RDT_UNAVAILABLE, 'X')
    rdt_field.add_choice('en', RDTField.RDT_UNKOWN, 'U')

    def process(self, patient):
        '''Fever Section (6-59 months)'''
        self.rdt_field.set_language(self.message.reporter.language)
        if len(self.params) < 2:
            raise ParseError(_(u"Not enough info, expected (%s) (%s)") % \
                    (self.PREFIX, '/'.join(self.rdt_field.valid_choices())))

        if not self.rdt_field.is_valid_choice(self.params[1]):
            raise ParseError(_(u"RDT Result must be %(choices)s") % \
                              {'choices': self.rdt_field.choices_string()})

        days, weeks, months = patient.age_in_days_weeks_months()
        response = ''
        created_by = self.message.persistant_connection.reporter.chw

        if days <= 30:
            raise Inapplicable(_("Child is too young for treatment. "\
                        "Please refer IMMEDIATELY to clinic"))
        else:
            rdt = self.rdt_field.get_db_value(self.params[1])
            if rdt == RDTField.RDT_POSITIVE:
                years = months / 12
                tabs, yage = None, None
                # just reformatted to make it look like less ugh
                if years < 1:
                    if months < 2:
                        tabs, yage = None, None
                    else:
                        tabs, yage = 1, _("less than 3")
                elif years < 3:
                    tabs, yage = 1, _("less than 3")
                elif years < 9:
                    tabs, yage = 2, years
                elif years < 15:
                    tabs, yage = 3, years
                else:
                    tabs, yage = 4, years
                instructions = ''
                # no tabs means too young
                if not tabs:
                    raise Inapplicable(_("Child is too young for treatment. "\
                        "Please refer IMMEDIATELY to clinic"))
                else:
                    instructions = _("Child is %(age)s. Please provide "\
                                     "%(tabs)s tab%(plural)s of Coartem "\
                                     "(ACT) twice a day"\
                              " for 3 days") % {'age': yage, \
                                        'tabs': tabs, \
                                        'plural': (tabs > 1) and 's' or ''}

                response = instructions

                '''alert = \
                    _("MRDT> Child %(last_name)s, %(first_name)s, "\
                    "%(gender)s/%(age)s (%(zone)s) has MALARIA%(danger)s. "\
                          "CHW: ..." % info)'''

                expires_on = datetime.now() + timedelta(7)
                case = Case(patient=patient, expires_on=expires_on, \
                            type=Case.TYPE_FEVER)
                case.save()
            else:
                response = _('No fever')

            fr = FeverReport(created_by=created_by, rdt_result=rdt, \
                             patient=patient)
            fr.save()

        return response
    
