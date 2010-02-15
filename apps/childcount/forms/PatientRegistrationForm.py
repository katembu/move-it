#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re


from datetime import date

from django.db import models
from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.utils import clean_names, DOBProcessor
from childcount.models import Patient
from childcount.exceptions import BadValue, ParseError

from childcount.forms.utils import MultipleChoiceField


class PatientRegistrationForm(CCForm):
    KEYWORDS = {
        'en': ['new'],
    }
    MIN_HH_AGE = 10

    gender_field = MultipleChoiceField()
    gender_field.add_choice('en', Patient.GENDER_MALE, 'M')
    gender_field.add_choice('en', Patient.GENDER_FEMALE, 'F')

    SELF_HH = {}
    SELF_HH['en'] = 'P'

    SURNAME_FIRST = False

    def pre_process(self, health_id):

        chw = self.message.persistant_connection.reporter.chw
        try:
            p = Patient.objects.get(health_id=health_id)
            print p
        except Patient.DoesNotExist:
            pass
        else:
            raise BadValue(_(u"That health ID has already been registered to "\
                              "%(patient)s by %(chw)s") % \
                             {'patient': p, 'chw': p.chw})

        patient = Patient()
        patient.health_id = health_id
        patient.chw = chw
        patient.location = chw.location
        tokens = self.params[1:]

        lang = self.message.reporter.language

        expected = _(u"given_names surname gender age or date_of_birth " \
                      "and head_of_household")

        if len(tokens) < 4:
            raise ParseError(_(u"Not enough info. You must send: " \
                                "%(expected)") % {'expected': expected})

        self.gender_field.set_language(lang)

        gender_indexes = []
        i = 0
        for token in tokens:
            if token in self.gender_field.valid_choices():
                gender_indexes.append(i)
            i += 1

        if len(gender_indexes) == 0:
            raise ParseError(_(u"You must indicate gender after the name " \
                                "with a %(choices)s") % \
                              {'choices': self.gender_field.choices_string()})


        if tokens[-1] == self.SELF_HH[lang].lower():
            print 'xxxxxxxxxxx'
            patient.household = patient
        else:
            try:
                patient.household = Patient.objects.get(health_id=tokens[-1])
            except Patient.DoesNotExist:
                if DOBProcessor.is_valid_dob_or_age(lang, \
                                                    ' '.join(tokens[-1])):
                    raise ParseError(_(u"You must indicate the head of " \
                                        "household after the age. If this " \
                                        "is the head of household " \
                                        "write %(char)s after age.") % \
                                        {'char': self.SELF_HH[lang]})
                else:
                    raise BadValue(_(u"Could not find head of household " \
                                      "with health ID %(id)s. You must " \
                                      "register the head of household " \
                                      "first") % \
                                      {'id': tokens[-1]})

            age = patient.household.years()
            if age < self.MIN_HH_AGE:
                raise BadValue(_(u"The head of household you specified is " \
                                  "too young to be a head of household " \
                                  "(%(hh)s)") % {'hh': patient.household})

        # remove head of household
        tokens.pop()
        for i in gender_indexes:
            dob, variance = DOBProcessor.from_age_or_dob(lang, \
                                                     ' '.join(tokens[i + 1:]))
            if dob:
                patient.dob = dob
                days, weeks, months = patient.age_in_days_weeks_months()
                if days < 60 and variance > 1:
                    raise BadValue(_(u"Please provide an exact birth date " \
                                      "for children under 2 months"))
                elif months < 24 and variance > 30:
                    raise BadValue(_(u"Please provide an exact birth date " \
                                      "or the age in months for children " \
                                      "under two years"))

        if not dob:
            raise ParseError(_(u"Could not understand your message. " \
                                "%(expected)s") % {'expected': expected})

        if patient.household == patient and patient.years() < self.MIN_HH_AGE:
            raise BadValue(_(u"This patient is too young to be a head of " \
                              "household. Please indicate their head of" \
                              "household"))

        patient.estimated_dob = variance > 1

        # remove the age tokens
        tokens = tokens[:i + 1]

        patient.gender = self.gender_field.get_db_value(tokens.pop())

        patient.last_name, patient.first_name, alias = \
                             clean_names(' '.join(tokens), \
                             surname_first=self.SURNAME_FIRST)


        patient_check = Patient.objects.filter(first_name=patient.first_name, \
                                               last_name=patient.last_name, \
                                               dob=patient.dob)
        if len(patient_check) > 0:
            old_p = patient_check[0]
            if old_p.chw == chw:
                patient_chw = _(u"you")
            else:
                patient_chw = patient_check[0].chw
            raise BadValue(_(u"%(name)s %(sex)s/%(age)s was already " \
                              "registered by %(chw)s. Their health id is " \
                              "%(id)s") % \
                              {'name': old_p.full_name(), \
                               'sex': old_p.gender, \
                               'age': old_p.humanised_age(), \
                               'chw': patient_chw, \
                               'id': old_p.health_id.upper()})
        patient.save()

        # For some reason django doesn't do this properly until the patient
        # record is saved.
        if patient.household == patient:
            patient.household = patient
            patient.save()

        response = _("You successfuly registered %(patient)s") % \
                    {'patient': patient}
        return response
