#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Child logic
'''

from django.utils.translation import ugettext_lazy as _

from childcount.models import Patient, Referral
from childcount.models.reports import NewbornReport, ChildReport
from childcount.models.Case import Case


def new_born_section(created_by, patient, danger_signs, clinic_vists):
    '''1.1) Newborn Section (0-30 days) (REQUIRED)'''
    days, months = patient.age_in_days_months()
    response = ''

    if months >= 6 and months < 60:
        response = _('Child is %(months)d months old. Please fill out CHILD ' \
                     '(+C) form') % {'months': months}
    elif months > 59:
        response = _('Child is older then 59 months.')
    else:
        if danger_signs.upper() == 'Y':
            #create a referral
            rf = Referral(patient=patient)
            rf.save()
            response = _('Please refer child immediately to clinic '\
                         '(#%(refid)s)') % {'refid': rf.referral_id}
        else:
            response = _('Clinic visit %(visits)s registered for newborn.') % \
                        {'visits': clinic_vists}
        nr = NewbornReport(created_by=created_by, patient=patient, \
                           clinic_vists=clinic_vists)
        nr.save()

    return response


def child_section(created_by, patient, fever, diarrhea, fever_form=False, \
                  diarrhea_form=False):
    '''1.3) Child Section (6-59 Months) (REQUIRED)'''

    days, months = patient.age_in_days_months()
    response = ''

    if months < 6:
        response = _('Child is an Infant. Please fill out Newborn ' \
                     '(+N) form')
    elif months > 59:
        response = _('Child is older then 59 months.')
    else:
        if fever.upper() == 'F' and not fever_form:
            response = _('Please check child for malaria and shortness of '\
                         'breath using the fever (F+) Form.')
        if diarrhea.upper() == 'D' and not diarrhea_form:
            response += _('Please treat child for diarrhea with ORS and Zinc'\
                          ' and record with ORS (+S) form')
        cr = ChildReport(created_by=created_by, patient=patient, \
                           fever=fever, diarrhea=diarrhea)
        cr.save()

    return response
