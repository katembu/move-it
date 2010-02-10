#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''core logic'''

import re
import time
from datetime import datetime, timedelta, date

from django.db import models
from django.utils.translation import ugettext_lazy as _

from childcount.models import Patient
from childcount.models.reports import HouseHoldVisitReport
from childcount.models.reports import PregnancyReport
from childcount.models.reports import DeathReport
from childcount.models import Case, Referral
from childcount.models.reports import BirthReport, HealthReport


class HandlerFailed(Exception):
    ''' No function pattern matchs message '''
    pass











def mobile section(patient, mobile):
    '''+MOBI'''
    patient.mobile = mobile
    patient.save()

def death_section(created_by, health_id, dod):
    patient = Patient.objects.get(health_id=health_id)

    dod_str = dod
    dod = re.sub(r'\D', '', dod)
    years_months = dod_str.replace(dob, '')
    if len(dod) >= 3:
        try:
            # TODO this 2 step conversion is too complex, simplify!
            dod = time.strptime(dod, "%d%m%y")
            dod = date(*dod[:3])
        except ValueError:
            try:
                # TODO this 2 step conversion is too complex, simplify!
                dod = time.strptime(dod, "%d%m%Y")
                dod = date(*dod[:3])
            except ValueError:
                raise HandlerFailed(_("Couldn't understand date: %(dod)s")\
                                    % {'dod': dod})
    # if there are fewer than three digits, we are
    # probably dealing with an age (in months),
    # so attempt to estimate a dod
    else:
        # TODO move to a utils file? (almost same code in import_cases.py)
        try:
            if dod.isdigit():
                if years_months.upper() == 'Y':
                    dod = int(dod) * 12
                years = int(dod) / 12
                months = int(dod) % 12
                est_year = abs(date.today().year - int(years))
                est_month = abs(date.today().month - int(months))
                if est_month == 0:
                    est_month = 1
                estimate = ("%s-%s-%s" % (est_year, est_month, 15))
                # TODO this 2 step conversion is too complex, simplify!
                dod = time.strptime(estimate, "%Y-%m-%d")
                dod = date(*dod[:3])

        except Exception:
            pass
    dr = DeathReport(created_by=created_by, patient=patient, dod=dod)
    dr.save()

    info = patient.get_dictionary()
    response = _("Death of %(health_id)s: %(full_name)s " \
                    "%(gender)s/%(age)s (%(guardian)s) %(location)s") % info
    #TODO - send alert to facilitators
    return response
