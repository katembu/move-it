#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

'''core logic'''

import re
import time
from datetime import datetime, timedelta, date

from django.db import models
from django.utils.translation import ugettext_lazy as _

from childcount.core.models.Patient import Patient
from childcount.core.models.Reports import HouseHoldVisitReport
from childcount.core.models.Reports import PregnancyReport
from childcount.core.models.Case import Case
from childcount.child.models import BirthReport


class HandlerFailed(Exception):
    ''' No function pattern matchs message '''
    pass


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


def newregistration_section(created_by, health_id, token_string):
    whitespace = re.compile('(\s+)')
    clean_token_string = re.sub(whitespace, " ", token_string)

    # split clean_token_string by spaces
    tokens = clean_token_string.split(" ")

    # create empty strings we can add to
    patient_name = ""
    guardian_name = ""
    # declare contact, since its optional
    contact = ""
    for token in tokens[:4]:

        # any tokens more than one non-digit character are probably parts
        # of the patient's name, so add to patient_name and
        # remove from tokens list
        test_age = re.match(r'(\d{1,6}[a-z]*)', token, re.IGNORECASE)

        if len(token) > 1 and not token.isdigit() and test_age is None:
            patient_name = patient_name \
                           + (tokens.pop(tokens.index(token))) + " "

    for token in tokens:
        # attempt to match gender
        gender_matches = re.match(r'[mf]', token, re.IGNORECASE)
        if gender_matches is not None:
            gender = token
            continue

        # attempt to match date of birth or age in months
        # if token is more than six digits, save as guardian's contact
        # this should match up between one and six digits, followed by an
        # optional word (e.g., 020301, 22m, 22mo)
        date_or_age = re.match(r'(\d{1,6}[a-z]*)', token, re.IGNORECASE)
        if date_or_age is not None:
            # only save if its less than six digits
            # which might sometimes match this
            if len(token) <= 6:
                dob = token
                continue
    
    tokens.pop(tokens.index(dob))
    tokens.pop(tokens.index(gender))
    gender = gender.upper()

    household_id = None
    if len(tokens) == 1:
        care_giver = tokens.pop()
        if token.upper() == 'P':
            care_giver = health_id
    else:
        care_giver = tokens.pop()
        household_id = tokens.pop()

    estimated_dob = False
    dob_str = dob
    dob = re.sub(r'\D', '', dob)
    years_months = dob_str.replace(dob, '')
    # if there are three or more digits, we are
    # probably dealing with a date
    if len(dob) >= 3:
        try:
            # TODO this 2 step conversion is too complex, simplify!
            dob = time.strptime(dob, "%d%m%y")
            dob = date(*dob[:3])
        except ValueError:
            try:
                # TODO this 2 step conversion is too complex, simplify!
                dob = time.strptime(dob, "%d%m%Y")
                dob = date(*dob[:3])
            except ValueError:
                raise HandlerFailed(_("Couldn't understand date: %(dob)s")\
                                    % {'dob': dob})
    # if there are fewer than three digits, we are
    # probably dealing with an age (in months),
    # so attempt to estimate a dob
    else:
        # TODO move to a utils file? (almost same code in import_cases.py)
        try:
            if dob.isdigit():
                if years_months.upper() == 'Y':
                    dob = int(dob) * 12
                years = int(dob) / 12
                months = int(dob) % 12
                est_year = abs(date.today().year - int(years))
                est_month = abs(date.today().month - int(months))
                if est_month == 0:
                    est_month = 1
                estimate = ("%s-%s-%s" % (est_year, est_month, 15))
                # TODO this 2 step conversion is too complex, simplify!
                dob = time.strptime(estimate, "%Y-%m-%d")
                dob = date(*dob[:3])

                estimated_dob = True
        except Exception, e:
            pass
    
    first, sep, last = patient_name.rstrip().rpartition(' ')
    first, sep, middle = first.rstrip().rpartition(' ')
    if first == '':
        first = middle
        middle = ''

    try:
        guardian = Patient.objects.get(health_id=care_giver)
    except models.ObjectDoesNotExist:
        guardian = None

    household = None
    if household_id is not None:
        try:
            household = Patient.objects.get(health_id=household_id)
        except models.ObjectDoesNotExist:
            pass

    if guardian is not None and household is None:
        household = guardian
    info = {}
    info.update({'first_name': first, 'last_name': last, \
                 'middle_name': middle, 'chw': created_by, 'gender': gender, \
                 'dob': dob, 'estimated_dob': estimated_dob, \
                 'health_id': health_id, 'guardian': guardian, \
                 'household': household})

    patient_check = Patient.objects.filter(first_name=info['first_name'], \
                                     last_name=info['last_name'], \
                                     chw=info['chw'], \
                                     dob=info['dob'])
    if patient_check:
        patient = patient_check[0]
        response = _("%(last_name)s, %(first_name)s (+%(health_id)s) " \
                            "has already been registered by %(chw)s.") \
                            % info
    else:
        patient = Patient(**info)
        patient.save()
        response = _("New +%(health_id)s: %(last_name)s, %(first_name)s " \
                    "%(gender)s/%(age)s (%(guardian)s) %(location)s") % info
    return response


def birth_section(created_by, health_id, token_string):
    whitespace = re.compile('(\s+)')
    clean_token_string = re.sub(whitespace, " ", token_string)

    # split clean_token_string by spaces
    tokens = clean_token_string.split(" ")

    # create empty strings we can add to
    patient_name = ""
    guardian_name = ""
    # declare contact, since its optional
    contact = ""
    for token in tokens[:4]:

        # any tokens more than one non-digit character are probably parts
        # of the patient's name, so add to patient_name and
        # remove from tokens list
        test_age = re.match(r'(\d{1,6}[a-z]*)', token, re.IGNORECASE)

        if len(token) > 1 and not token.isdigit() and test_age is None:
            patient_name = patient_name \
                           + (tokens.pop(tokens.index(token))) + " "

    for token in tokens:
        # attempt to match gender
        gender_matches = re.match(r'[mf]', token, re.IGNORECASE)
        if gender_matches is not None:
            gender = token
            continue

        # attempt to match date of birth or age in months
        # if token is more than six digits, save as guardian's contact
        # this should match up between one and six digits, followed by an
        # optional word (e.g., 020301, 22m, 22mo)
        date_or_age = re.match(r'(\d{1,6}[a-z]*)', token, re.IGNORECASE)
        if date_or_age is not None:
            # only save if its less than six digits
            # which might sometimes match this
            if len(token) <= 6:
                dob = token
                continue
    
    tokens.pop(tokens.index(dob))
    tokens.pop(tokens.index(gender))
    gender = gender.upper()

    for token in tokens:
        if len(token) > 4:
            care_giver = token
            continue
    tokens.pop(tokens.index(care_giver))
    
    #last three tokens
    small = tokens.pop()
    bcg = tokens.pop()
    clinic_delivery = tokens.pop()
    
    if bcg not in BirthReport.BCG_CHOICES:
        raise HandlerFailed(_('BCG choice `%(bcg)s` is UNKNOWN') % \
                            {'bcg': bcg})
    if small not in BirthReport.SMALL_CHOICES:
        raise HandlerFailed(_('Small baby choice `%(small)s` is UNKNOWN') % \
                            {'small': small})
    if clinic_delivery not in BirthReport.CLINIC_DELIVERY_CHOICES:
        raise HandlerFailed(_('Delivered in health facility choice '\
                              '`%(clinic_delivery)s` is UNKNOWN') % \
                            {'clinic_delivery': clinic_delivery})

    estimated_dob = False
    dob_str = dob
    dob = re.sub(r'\D', '', dob)
    years_months = dob_str.replace(dob, '')
    # if there are three or more digits, we are
    # probably dealing with a date
    if len(dob) >= 3:
        try:
            # TODO this 2 step conversion is too complex, simplify!
            dob = time.strptime(dob, "%d%m%y")
            dob = date(*dob[:3])
        except ValueError:
            try:
                # TODO this 2 step conversion is too complex, simplify!
                dob = time.strptime(dob, "%d%m%Y")
                dob = date(*dob[:3])
            except ValueError:
                raise HandlerFailed(_("Couldn't understand date: %(dob)s")\
                                    % {'dob': dob})
    # if there are fewer than three digits, we are
    # probably dealing with an age (in months),
    # so attempt to estimate a dob
    else:
        # TODO move to a utils file? (almost same code in import_cases.py)
        try:
            if dob.isdigit():
                if years_months.upper() == 'Y':
                    dob = int(dob) * 12
                years = int(dob) / 12
                months = int(dob) % 12
                est_year = abs(date.today().year - int(years))
                est_month = abs(date.today().month - int(months))
                if est_month == 0:
                    est_month = 1
                estimate = ("%s-%s-%s" % (est_year, est_month, 15))
                # TODO this 2 step conversion is too complex, simplify!
                dob = time.strptime(estimate, "%Y-%m-%d")
                dob = date(*dob[:3])

                estimated_dob = True
        except Exception, e:
            pass
    
    first, sep, last = patient_name.rstrip().rpartition(' ')
    first, sep, middle = first.rstrip().rpartition(' ')
    if first == '':
        first = middle
        middle = ''

    try:
        guardian = Patient.objects.get(health_id=care_giver)
    except models.ObjectDoesNotExist:
        guardian = None

    household = None
    if household_id is not None:
        try:
            household = Patient.objects.get(health_id=household_id)
        except models.ObjectDoesNotExist:
            pass

    if guardian is not None and household is None:
        household = guardian
    info = {}
    info.update({'first_name': first, 'last_name': last, \
                 'middle_name': middle, 'chw': created_by, 'gender': gender, \
                 'dob': dob, 'estimated_dob': estimated_dob, \
                 'health_id': health_id, 'guardian': guardian, \
                 'household': household})

    patient_check = Patient.objects.filter(first_name=info['first_name'], \
                                     last_name=info['last_name'], \
                                     chw=info['chw'], \
                                     dob=info['dob'])
    if patient_check:
        patient = patient_check[0]
        response = _("%(last_name)s, %(first_name)s (+%(health_id)s) " \
                            "has already been registered by %(chw)s.") \
                            % info
    else:
        patient = Patient(**info)
        patient.save()
        
        br = BirthReport(patient=patient, clinic_delivery=clinic_delivery, \
                         bcg=bcg, small=small, created_by=created_by)
        br.save()
        response = _("Birth %(health_id)s: %(last_name)s, %(first_name)s " \
                    "%(gender)s/%(age)s (%(guardian)s) %(location)s") % info
    return response
