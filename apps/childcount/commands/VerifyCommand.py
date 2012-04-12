#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

import re, random
from datetime import date, datetime

from django.db import models
from django.utils.translation import ugettext as _

from locations.models import Location

from childcount.utils import clean_names, DOBProcessor, random_id
from childcount.utils import send_alert, authenticated, servelet

from childcount.models import Patient, CHW

from childcount.exceptions import BadValue, ParseError

from childcount.commands import CCCommand


class VerifyCommand(CCCommand):
    """ Verify Command
    Params:
        * EVENT ID
        * NOTIFICATION NO
    """

    KEYWORDS = {
        'en': ['ver', 'v', 'valid'],
    }

    @authenticated
    def process(self):
        chw = self.message.reporter.chw
        lang = self.message.reporter.language

        #Check if CHW has permission i.e Chief, Assistant Chief
        groups = ("Assistant Chief", "Chief")
        reporters = CHW.objects.filter(user_ptr__groups__name__in=groups)

        if chw not in reporters:
            raise ParseError(_(u"Youre not allowed to verify events "))

        expected = _(u"EVENTID | Notification number")
        if len(self.params) < 3:
            raise ParseError(_(u"Not enough information. Expected: " \
                                "%(keyword)s %(expected)s") % \
                                {'keyword': self.params[0], \
                                'expected': expected})

        tokens = self.params[1:]

        event_id = tokens.pop(0)
        try:
            patient = Patient.objects.get(health_id=event_id)
        except Patient.DoesNotExist:
            raise BadValue(_(u"%(event_id)s is not a valid event id. You " \
                              "must indicate valid event id ") % \
                              {'event_id': event_id})

        #Notification number
        noti_number = ''.join(tokens[0])
        #noti_number = re.sub('\D', '', noti_number)
        if(len(noti_number) < 2):
            raise ParseError(_(u"Notification number is too short"))
        if len(noti_number) > 10:
            raise BadValue(_(u"Notification number cannot be longer "\
                                  "than 10 digits."))
        if noti_number:
            patient.notification_no = noti_number

        patient.cert_status = Patient.CERT_VERIFIED

        patient.save()

        self.message.respond(_("You successfuly verified %(patient)s ")   \
                                 %  {'patient': patient }, 'success')


        #The CHW manager should recived verified births only
        #Send alert to Managers and not self
        if patient.notification_no == Patient.CERT_VERIFIED:
            if patient.chw.manager and patient.chw.manager != chw:
                if patient.event_type ==1:
                    evnt  = "Verified Birth"
                else:
                    evnt = "Verified Death"
                msg = _(u"%(child)s, %(location)s CHW no: %(mobile)s") % \
                         {'child': patient, \
                          'location': patient.location.name, \
                          'mobile': patient.chw.connection().identity }

                msg=_(" Alert! ")+msg
                send_alert(chw.manager, msg=evnt+msg, name = "alert")


        #PUSH TO OXD death object
        servelet(patient.pk)
