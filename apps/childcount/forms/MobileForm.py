#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import re

from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.exceptions import BadValue


class MobileForm(CCForm):
    KEYWORDS = {
        'en': ['mob', 'mobile'],
    }

    def process(self, patient):
        mobile = ''.join(self.params[1:])
        mobile = re.sub('\D', '', mobile)
        if len(self.params) < 2 or not mobile.isdigit():
            raise BadValue(_('Expected phone number'))

        if len(mobile) > 16:
            raise BadValue(_('Phone number cannot be longer than 16 digits'))
        patient.mobile = mobile
        patient.save()
        self.response = _(u"Mobile phone number: %(mobile)s") % \
                          {'mobile': mobile}
