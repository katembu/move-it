#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re
from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.exceptions import ParseError, BadValue, Inapplicable
from childcount.models.reports import BirthReport
from childcount.forms.utils import MultipleChoiceField


class BirthForm(CCForm):
    KEYWORDS = {
        'en': ['birth'],
    }
    MIN_BIRTH_WEIGHT = 1
    MAX_BIRTH_WEIGHT = 6

    def process(self, patient):

        cd_field = MultipleChoiceField()
        cd_field.add_choice('en', BirthReport.CLINIC_DELIVERY_YES, 'Y')
        cd_field.add_choice('en', BirthReport.CLINIC_DELIVERY_NO, 'N')
        cd_field.add_choice('en', BirthReport.CLINIC_DELIVERY_UNKOWN, 'U')

        breastfed_field = MultipleChoiceField()
        breastfed_field.add_choice('en', BirthReport.BREASTFED_YES, 'Y')
        breastfed_field.add_choice('en', BirthReport.BREASTFED_NO, 'N')
        breastfed_field.add_choice('en', BirthReport.BREASTFED_UNKOWN, 'U')

        chw = self.message.persistant_connection.reporter.chw

        days, weeks, months = patient.age_in_days_weeks_months()
        humanised = patient.humanised_age()
        if days > 28:
            raise Inapplicable(_(u"Patient is %(age)s old. You cannot " \
                                  "submit birth reports for patients over " \
                                  "28 days old") % {'age': humanised})

        try:
            br = BirthReport.objects.filter(patient=patient)
        except BirthReport.DoesNotExist:
            pass
        else:
            raise Inapplicable(_(u"A birth report for %(p)s was already " \
                                  "submited by %(chw)s") % \
                                  {'p': patient, 'chw': chw})

        if len(self.params) < 3:
            raise ParseError(_(u"Not enough information, expected: " \
                                "(delivered in health facility) (breasfed " \
                                "within an hour of birth) " \
                                "weight(kg)(optional)"))


        cd_field.set_language(chw.language)
        breastfed_field.set_language(chw.language)
        clinic_delivery = self.params[1]
        if not cd_field.is_valid_choice(clinic_delivery):
            raise BadValue(_(u"|Delivered in health facility?| must be " \
                              "%(choices)s") % \
                              {'choices': cd_field.choices_string()})
        cd_db = cd_field.get_db_value(clinic_delivery)

        breastfed = self.params[2]
        if not breastfed_field.is_valid_choice(breastfed):
            raise BadValue(_(u"|Breastfed within an hour of birth?| must be " \
                              "%(choices)s") % \
                            {'choices': breastfed_field.choices_string()})
        breastfed_db = breastfed_field.get_db_value(breastfed)

        weight = None
        if len(self.params) > 3:
            regex = r'(?P<w>\d+(\.?\d*)?).*'
            match = re.match(regex, self.params[3])
            if match:
                weight = float(match.groupdict()['w'])
                if weight > self.MAX_BIRTH_WEIGHT:
                    raise BadValue(_(u"Birth weight can not be greater than " \
                                      "%(max)skg") % \
                                     {'max': self.MAX_BIRTH_WEIGHT})
                if weight < self.MIN_BIRTH_WEIGHT:
                    raise BadValue(_(u"Birth weight can not be less than " \
                                      "%(min)skg") % \
                                     {'min': self.MIN_BIRTH_WEIGHT})
            else:
                raise ParseError(_(u"Unkown value. Weight should be a number"))


        if cd_db == BirthReport.CLINIC_DELIVERY_YES:
            cd_string = _(u"Delivered in health facility")
        elif cd_db == BirthReport.CLINIC_DELIVERY_NO:
            cd_string = _(u"Home delivery")
        elif cd_db == BirthReport.CLINIC_DELIVERY_UNKOWN:
            cd_string = _(u"Unkown delivery location")

        if breastfed_db == BirthReport.BREASTFED_YES:
            bf_string = _(u"Breastfed at birth")
        elif breastfed_db == BirthReport.BREASTFED_NO:
            bf_string = _(u"Did not breastfeed at birth")
        elif breastfed_db == BirthReport.BREASTFED_UNKOWN:
            bf_string = _(u"Unkown breastfeeding at birth")

        self.response = '%s, %s' % (cd_string, bf_string)
        if weight:
            self.response += _(", %(weight)skg birth weight") % \
                              {'weight': weight}

        form = BirthReport(created_by=chw, patient=patient, \
                           clinic_delivery=cd_db, \
                           breastfed=breastfed_db, weight=weight)

        form.save()
