#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.utils.translation import ugettext as _

from childcount.forms import CCForm


class MobileForm(CCForm):
    KEYWORDS = {
        'en': ['mobi'],
    }

    def process(self, patient):
        if len(self.params) < 2:
            return False
        response = _('Mobile Ok')
        patient.mobile = self.params[1]
        patient.save()
        return response
