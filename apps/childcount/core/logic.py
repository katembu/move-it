#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''core logic'''

from datetime import datetime, timedelta

from django.utils.translation import ugettext_lazy as _

from childcount.core.models.Patient import Patient
from childcount.core.models.Reports import HouseHoldVisitReport
from childcount.core.models.Reports import PregnancyReport
from childcount.core.models.Case import Case


def housholdvisit_section(created_by, health_id, available):
    '''2.1) HH Visit - All Households'''
    patient = Patient.objects.get(health_id=health_id)

    if available.upper() == 'Y':
        available = True
    else:
        available = False
    hhvr = HouseHoldVisitReport(created_by=created_by, patient=patient, \
                                available=available)
    hhvr.save()
    return _('Visist registered to %(full_name)s. Thank you.') % \
                    patient.get_dictionary()


def pregnancy_section(created_by, health_id, clinic_visits, month, fever):
    '''3.2 Pregnancy Section'''
    patient = Patient.objects.get(health_id=health_id)
    response = ''
    if month in range(1, 9) and clinic_visits in range(0,9):
        pcases = Case.objects.filter(patient=patient, \
                                     type=Case.TYPE_PREGNANCY, \
                                     status=Case.STATUS_OPEN)

        if pcases.count() == 0:
            #create a new pregnancy case
            now = datetime.now()
            #expected birth date
            expires_on = now - timedelta(int((9 - month) * 30.4375))
            case = Case(patient=patient, type=Case.TYPE_PREGNANCY, \
                 expires_on=expires_on)
            case.save()
        else:
            case = pcases.pop()

        if fever.upper() == 'Y':
            if month <= 3:
                response = _('Please refer woman immediately to clinic for '\
                    'treatment. Do not test with RDT or provide home-based '\
                    'treatment.')
            fever = True
        else:
            fever = False

        if month == 2 and clinic_visits < 1 \
            or month == 5 and clinic_visits < 2 \
            or month == 7 and clinic_visits < 3 \
            or month == 8 and clinic_visits < 8:
            response += _('Remind the woman she is due for a clinic visit')

        pr = PregnancyReport(created_by=created_by, patient=patient, \
                        pregnancy_month=month, clinic_visits=clinic_visits, \
                        fever=fever)
        pr.save()
        
        response += _('%(clinic_visits)s clinic visits, month %(month)s') % \
            {'clinic_visits': clinic_visits, 'month': month}
    else:
        response = _('Invalid data, month(1-9), visits(0-9)')

    return response
