#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

import re

from django.utils.translation import ugettext as _

from datetime import datetime, timedelta

from childcount.utils import send_alert

from childcount.forms import CCForm
from childcount.exceptions import BadValue

class UpdateMobileForm(CCForm):
    """ Mobile Phone number  Update

    Params:
        * phone number
    """

    KEYWORDS = {
        'en': ['mob', 'mobile'],
    }

    def process(self, patient):
        chw = self.message.reporter.chw

        #Upto 30 days of birth allow change
        date_created = patient.created_on
        if datetime.today() > (date_created + timedelta(30)):
            raise ParseError(_(u"Cannot update record that is 30 days old" \
                                " %(patient)s Registered on : %(reg)s  ") \
                                % {'patient': patient, 
                                   'reg': patient.created_on})

       
        mobile = ''.join(self.params[1:])
        mobile = re.sub('\D', '', mobile)
        if len(self.params) < 2 or not mobile.isdigit():
            raise BadValue(_(u"Expected: phone number."))

        if len(mobile) > 16:
            raise BadValue(_(u"Phone number cannot be longer than 16 digits."))
        patient.mobile = mobile
        patient.save()
        self.response = _(u"Mobile phone number: %(mobile)s") % \
                          {'mobile': mobile}

        #Send alert to Managers and not self
        if chw.manager and chw.manager != chw:
            msg = _(u"%(chw)s(%(mobile)s) changed mobile of %(person)s  " \
                     " to: %(pnew)s") % \
                     {'chw': chw, \
                      'person': patient, \
                      'pnew': mobile, \
                      'mobile': chw.connection().identity }

            msg=_("UMOBILE Alert!")+msg
            send_alert(chw.manager, msg, name = "Death Alert")
