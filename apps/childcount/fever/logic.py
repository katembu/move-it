#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Nutrition Logic'''

from datetime import datetime, timedelta

from django.utils.translation import ugettext_lazy as _

from childcount.core.models.Patient import Patient
from childcount.core.models.Case import Case
from childcount.fever.models import FeverReport
from childcount.core.models.SharedFields import RDTField

def fever_section(created_by, health_id, rdt):
    '''Fever Section (6-59 months)'''
    patient = Patient.objects.get(health_id=health_id)
    days, months = patient.age_in_days_months()
    response = ''

    if days <= 30:
        response =  _("Child is too young for treatment. "\
                    "Please refer IMMEDIATELY to clinic")
    elif months > 59:
        response = _('Child is older then 59 months. For any concerns about '\
                     'child in the future please go to the clinic. (Please '\
                     'advise mother to still closely monitor child and refer '\
                     'them to the clinic any time there is a concern). '\
                     'Positive reinforcement')
    else:
        if rdt.upper() in ('Y', 'P'):
            years = months/12
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
    
            # no tabs means too young
            if not tabs:
                response = _("Child is too young for treatment. "\
                    "Please refer IMMEDIATELY to clinic")
            else:
                response  = \
                        _("Child is %(age)s. Please provide %(tabs)s"\
                          " tab%(plural)s of Coartem (ACT) twice a day"\
                          " for 3 days") % {'age': yage, \
                                    'tabs': tabs, \
                                    'plural': (tabs > 1) and 's' or ''}

            info = {}
            info.update({'last_name': patient.last_name,
                         'first_name': patient.first_name,
                         'age': patient.age(),
                         'gender': patient.gender,
                         'zone': patient.zone})
            info.update({'instructions': response})
            # finally build out the messages
            response = _("MRDT> Child %(last_name)s, %(first_name)s, "\
                "%(gender)s/%(age)s has MALARIA. %(instructions)s"\
                 % info)

            alert = \
                _("MRDT> Child %(last_name)s, %(first_name)s, "\
                "%(gender)s/%(age)s (%(zone)s) has MALARIA%(danger)s. "\
                      "CHW: ..." % info)

            expires_on = datetime.now() + timedelta(7)
            case = Case(patient=patient, expires_on=expires_on)
            case.save()
        if rdt in RDTField.RDT_CHOICES:
            fr = FeverReport(created_by=created_by, rdt_result=rdt)
            fr.save()
        else:
            response = _('Unknown choice')
    return response
