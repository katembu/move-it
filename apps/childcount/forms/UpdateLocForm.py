#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

import re

from django.utils.translation import ugettext as _

from datetime import datetime, timedelta

from childcount.utils import send_alert

from childcount.forms import CCForm
from childcount.exceptions import BadValue
from locations.models import Location

class UpdateLocForm(CCForm):
    """ Location Update

    Params:
        * Location
    """

    KEYWORDS = {
        'en': ['loc', 'location'],
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

        #OLD Location Name        
        old_loc = patient.location.name

        tokens = self.params[1:]

        location_code = tokens.pop(0)
        try:
            location = Location.objects.get(code__iexact=location_code)
        except Location.DoesNotExist:
            raise BadValue(_(u"%(loc)s is not a valid location code. You " \
                              "must indicate location code " \
                              "before name.") % \
                              {'loc': location_code})

        #check if allowed to report for this location
        if chw.assigned_location.filter(id=location.pk).count() == 0:
            raise BadValue(_(u"Youre not authorised to send report for " \
                              " %(loc)s. Contact District Registry ") % \
                              {'loc': location.name.upper()})

        patient.location = location  
        patient.save()

        self.response = _(u"Location: %(loc)s") % \
                          {'loc': patient.location.name}

        #Send alert to Managers and not self
        if chw.manager and chw.manager != chw:
            msg = _(u"%(chw)s(%(mobile)s) changed location of %(person)s  " \
                     " from %(old_loc)s to: %(newloc)s") % \
                     {'chw': chw, \
                      'person': patient, \
                      'old_loc': old_loc, \
                      'newloc': patient.location.name, \
                      'mobile': chw.connection().identity }

            msg=_("UPDATE Alert!")+msg
            send_alert(chw.manager, msg, name = "UPDATE Alert")
