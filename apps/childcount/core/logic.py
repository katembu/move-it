#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''core logic'''

from datetime import datetime, timedelta

from django.utils.translation import ugettext_lazy as _

from childcount.core.models.Patient import Patient
from childcount.core.models.Reports import HouseHoldVisitReport


def housholdvisit_section(created_by, health_id, available):
    '''Fever Section (6-59 months)'''
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
