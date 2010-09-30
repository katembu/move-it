#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

from django.utils.translation import ugettext as _

from childcount.commands import CCCommand
from childcount.models import Patient
from childcount.utils import authenticated

class ChownCommand(CCCommand):
    ''' Change CHW for a patient set

        Format: chown FIRST_ID LAST_ID
        Sets all patients created between
        FIRST_ID and LAST_ID (inclusive)
        by the same CHW/Data entry clerk 
        to the current CHW.
    '''

    KEYWORDS = {
        'en': ['chown'],
        'fr': ['chown'],
    }

    @authenticated
    def process(self):

        # warn if no search criteria
        if self.params.__len__() < 3:
            self.message.respond(_(u"Lookup command requires a first and " \
                                   "last health ID."), 'error')
            return True

        terms = self.params[1:]
        first_id = terms[0].upper()
        last_id = terms[1].upper()

        first = None
        last = None

        # Lookup first health id
        try: 
            first = Patient.objects.get(health_id=first_id)
        except Patient.DoesNotExist:
            self.message.respond(_(u"There is no person with " \
                                    "ID %(hid)s.") % {'hid': first_id}, 'error')
            return True
 
        # Lookup last health id
        try: 
            last = Patient.objects.get(health_id=last_id)
        except Patient.DoesNotExist:
            self.message.respond(_(u"There is no person with " \
                                    "ID %(hid)s.") % {'hid': last_id}, 'error')
            return True
  
        if first.chw.pk != last.chw.pk:
            self.message.respond(_(u"Patients %(first)s and %(last)s have " \
                                    "different CHWs.  (First CHW: %(fchw)s " \
                                    "Last CHW: %(lchw)s)") % 
                                    {'first': first.health_id.upper(),
                                    'last': last.health_id.upper(),
                                    'fchw': first.chw, 'lchw': last.chw}, 'error')
            return True
        
        if first.created_on > last.created_on:
            self.message.respond(_(u"Patient %(fid)s was created " \
                "AFTER patient %(lid)s. You should send the earlier ID first " \
                "followed by the later ID.") % \
                    {'fid': first_id, 'lid': last_id},
                'error')
            return True

        matches = Patient.objects\
            .filter(chw=first.chw.pk)\
            .filter(created_on__gte=first.created_on)\
            .filter(created_on__lte=last.created_on)

        if matches.count() == 0:
            self.message.respond(\
                _(u"There were 0 patients created by CHW %(chw)s " \
                "between %(fdate)s and %(ldate)s.") \
                % {'chw': unicode(first.chw),
                    'fdate': unicode(first.created_on),
                    'ldate': unicode(last.created_on)}, \
                'error')

            return True

        nrows = matches.update(chw = \
            self.message.persistant_connection.reporter.chw)

        self.message.respond(\
            _(u"Changed CHW for %(n)d patients to %(chw)s") \
                % {'n': nrows, 
                    'chw': unicode(self.message.\
                    persistant_connection.reporter.chw)},
            'success')
        return True
