#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re
from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.exceptions import ParseError, BadValue, Inapplicable
from childcount.models.reports import FollowUpReport
from childcount.forms.utils import MultipleChoiceField


class FollowUpForm(CCForm):
    KEYWORDS = {
        'en': ['u'],
    }

    def process(self, patient):

        imp_field = MultipleChoiceField()
        imp_field.add_choice('en', FollowUpReport.IMPROVEMENT_YES, 'Y')
        imp_field.add_choice('en', FollowUpReport.IMPROVEMENT_NO, 'N')
        imp_field.add_choice('en', FollowUpReport.IMPROVEMENT_UNKOWN, 'U')
        imp_field.add_choice('en', FollowUpReport.IMPROVEMENT_UNAVAILABLE, 'L')

        v_field = MultipleChoiceField()
        v_field.add_choice('en', FollowUpReport.VISITED_YES, 'Y')
        v_field.add_choice('en', FollowUpReport.VISITED_NO, 'N')
        v_field.add_choice('en', FollowUpReport.VISITED_UNKOWN, 'U')
        v_field.add_choice('en', FollowUpReport.VISITED_INPATIENT, 'P')

        chw = self.message.persistant_connection.reporter.chw

        if len(self.params) < 3:
            raise ParseError(_(u"Not enough information, expected: " \
                                "| Improvement? | Visited facility? | "))

        imp_field.set_language(chw.language)
        imp = self.params[1]
        if not imp_field.is_valid_choice(imp):
            raise BadValue(_(u"| Improvement? | Must be " \
                              "%(choices)s") % \
                              {'choices': imp_field.choices_string()})
        imp_db = imp_field.get_db_value(imp)

        v_field.set_language(chw.language)
        v = self.params[2]
        if not v_field.is_valid_choice(v):
            raise BadValue(_(u"| Visited facility? | Must be " \
                              "%(choices)s") % \
                              {'choices': v_field.choices_string()})
        v_db = v_field.get_db_value(v)


        if imp_db == FollowUpReport.IMPROVEMENT_YES:
            imp_string = _(u"Condition improved")
        elif imp_db == FollowUpReport.IMPROVEMENT_NO:
            imp_string = _(u"Condition did not improve")
        elif imp_db == FollowUpReport.IMPROVEMENT_UNKOWN:
            imp_string = _(u"Condition improvement unkown")
        elif imp_db == FollowUpReport.IMPROVEMENT_UNAVAILABLE:
            imp_string = _(u"Patient unavailable")

        if v_db == FollowUpReport.VISITED_YES:
            v_string = _(u"Patient visited health facility")
        elif v_db == FollowUpReport.VISITED_NO:
            v_string = _(u"Patient did not visit health facility")
        elif v_db == FollowUpReport.VISITED_UNKOWN:
            v_string = _(u"Unkown whether patient visited health facility " \
                          "or not")
        elif v_db == FollowUpReport.VISITED_INPATIENT:
            v_string = _(u"Patient currently inpatient at health facility")

        self.response = imp_string + ', ' + v_string

        report = FollowUpReport(created_by=chw, patient=patient, \
                                improvement=imp_db, visited_clinic=v_db)

        report.save()
