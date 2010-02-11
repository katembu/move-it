#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.exceptions import BadValue


class MobileForm(CCForm):
    KEYWORDS = {
        'en': ['mob'],
    }

    def process(self, patient):
        if len(self.params) < 2:
            return False
        mobile = ''.join(self.params[1:])
        if not mobile.isdigit():
            raise BadValue(_('Expected numbers'))
        patient.mobile = mobile
        patient.save()
        response = _('mobile: %(mobile)s') % {'mobile': mobile} 
        return response
