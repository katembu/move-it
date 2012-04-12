#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu


from datetime import datetime, timedelta

from django.utils.translation import ugettext as _
from childcount.utils import clean_names, send_alert
from childcount.forms import CCForm
from childcount.models import Patient
from childcount.exceptions import ParseError, BadValue, Inapplicable


class UpdateNameForm(CCForm):
    """ Update Name
    Params:
        * first name
        * last name
    """
    KEYWORDS = {
        'en': ['name'],
    }

    SURNAME_FIRST = False

    def process(self, patient):
        chw = self.message.reporter.chw
        if len(self.params) < 3:
            raise ParseError(_(u"Not enough info. Expected: | First Name | " \
                                "Last Name |"))
        
        #Upto 30 days of birth allow change
        date_created = patient.created_on
        if datetime.today() > (date_created + timedelta(30)):
            raise ParseError(_(u"Cannot update record that is 30 days old" \
                                " %(patient)s Registered on : %(reg)s  ") \
                                % {'patient': patient, 
                                   'reg': patient.created_on})

       
        #hold  previous Name
        pname = _(u"%(fname)s %(lname)s ") % {'fname': patient.first_name, \
                   'lname': patient.last_name}
       
        #set New Name
        patient.last_name, patient.first_name, alias = \
                             clean_names(' '.join(self.params[1:]), \
                             surname_first=self.SURNAME_FIRST)

        #fetch new name
        newname = _(u" %(fname)s %(lname)s ") % {'fname': \
                   patient.first_name, 'lname': patient.last_name}

        patient.save()

        #display response
        self.response = _("You successfuly changed name of %(patient)s to "  \
                          "%(newname)s") % {'patient': pname,  \
                            'newname': newname}


        #Send alert to Managers and not self
        if chw.manager and chw.manager != chw:
            msg = _(u"%(chw)s(%(mobile)s) changed name of %(person)s  " \
                     " to: %(pnew)s") % \
                     {'chw': chw, \
                      'person': pname, \
                      'pnew': newname, \
                      'mobile': chw.connection().identity }

            msg=_("UNAME Alert!")+msg
            send_alert(chw.manager, msg, name = "Death Alert")
