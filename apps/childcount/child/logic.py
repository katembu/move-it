#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''Child logic
'''

from django.utils.translation import ugettext_lazy as _

from childcount.core.models.Patient import Patient
from childcount.core.models.Referral import Referral
from childcount.core.models.Reports import NewbornReport
  
def new_born_section(created_by, health_id, danger_signs, visits):
    '''1.1) Newborn Section (0-30 days) (REQUIRED)'''

    patient = Patient.objects.get(health_id=health_id)
    days, months = patient.age_in_days_months()
    response = ''

    if days > 30 and months < 6:
        response = _('Child is no longer a newborn. Please fill out INFANT ' \
                     '(+I) form')
    elif months > 6 and months < 60:
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
                        {'visits': visits}
        nr = NewbornReport(created_by=created_by, patient=patient, \
                           danger_signs=danger_signs)
        nr.save()

    return response
    
