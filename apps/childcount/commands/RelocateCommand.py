#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

import datetime

from django.utils.translation import ugettext as _

from locations.models import Location

from childcount.commands import CCCommand
from childcount.models import Patient, CHW
from childcount.utils import authenticated

class RelocateCommand(CCCommand):
    ''' Relocate a household
        
        Format: reloc LOC_CODE HEALTH_ID

        Relocates the household containing
        the patient HEALTH_ID to location
        LOC_CODE with the current CHW.
    '''

    KEYWORDS = {
        'en': ['reloc'],
        'fr': ['reloc'],
    }

    @authenticated
    def process(self):
        if 'encounter_date' not in self.message.__dict__:
            self.message.respond(_(u'Cannot run reloc command from '
                                    'cell phone. Use the computer interface '
                                    'instead.'), 'error')
            return True

        # warn if no search criteria
        if self.params.__len__() != 3:
            self.message.respond(_(u"Relocate command format: " \
                "reloc LOC HEALTH_ID."),
            'error')
            return True

        # lookup CHW
        try:
            new_chw = CHW.objects.get(pk = self.message.chw)
        except CHW.DoesNotExist:
            self.message.respond(_(u"CHW with ID %(id)d does not exist") % \
                {'id': self.message.chw})
            return True

        loc_code = self.params[1]
        health_id = self.params[2]

        # Lookup location code 
        location = None
        try: 
            location = Location.objects.get(code=loc_code)
        except Patient.DoesNotExist:
            self.message.respond(_(u"There is no location with code " \
                                    "%(code)s.") % {'code': loc_code}, 'error')
        # Lookup health id
        person = None
        try: 
            person = Patient.objects.get(health_id=health_id)
        except Patient.DoesNotExist:
            self.message.respond(_(u"There is no person with " \
                                    "ID %(hid)s.") % {'hid': health_id}, 'error')

        members = Patient\
            .objects\
            .filter(household__health_id=person.household.health_id)

        count = members.update(location=location)
        count = members.update(chw=new_chw)

        msg = _(u"Assigned %(count)d patients to %(loc)s with CHW %(chw)s: ") % \
            {'loc': location.code.upper(), \
            'chw': new_chw.full_name(), \
            'count': count}
        msg += ' '.join([p.health_id.upper() for p in members])

        self.message.respond(msg, 'success')
        return True
