#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import re
import time
from datetime import date

from django.db import models
from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.exceptions import BadValue
from childcount.models import Patient
from childcount.models.reports import BirthReport


class BirthForm(CCForm):
    KEYWORDS = {
        'en': ['birth'],
    }

    def pre_process(self, health_id):
        if len(self.params) < 4:
            return False
        response = ''
        created_by = self.message.persistent_connection.reporter.chw

        tokens = self.params
        #take out the keyword
        tokens.pop(tokens.index(self.params[0]))

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
        weight = tokens.pop()
        weight = re.sub(r'([a-z|A-Z])', '', weight)
        bcg = tokens.pop()
        clinic_delivery = tokens.pop()

        if bcg not in BirthReport.BCG_CHOICES:
            raise BadValue(_('BCG choice `%(bcg)s` is UNKNOWN') % \
                                {'bcg': bcg})
        if clinic_delivery not in BirthReport.CLINIC_DELIVERY_CHOICES:
            raise BadValue(_('Delivered in health facility choice '\
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
                    raise BadValue(_("Couldn't understand date: %(dob)s")\
                                        % {'dob': dob})
        # if there are fewer than three digits, we are
        # probably dealing with an age (in months),
        # so attempt to estimate a dob
        else:
            # TODO move to a utils file?
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
        if guardian is not None:
            try:
                household = guardian.household
            except:
                pass

        if guardian is not None and household is None:
            household = guardian
        info = {}
        info.update({'first_name': first, 'last_name': last, \
                     'middle_name': middle, 'chw': created_by, \
                     'gender': gender, \
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

            br = BirthReport(patient=patient, \
                             clinic_delivery=clinic_delivery, \
                             bcg=bcg, weight=weight, created_by=created_by)
            br.save()
            response = _("Birth %(health_id)s: %(last_name)s, %(first_name)s "\
                    "%(gender)s/%(age)s (%(guardian)s) %(location)s") % info
        return response
