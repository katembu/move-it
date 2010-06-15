#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from django.utils.translation import ugettext as _


from childcount.forms import CCForm
from childcount.models import Encounter
from childcount.models.reports import BedNetReport
from childcount.exceptions import ParseError, BadValue, Inapplicable
from childcount.forms.utils import MultipleChoiceField

class BedNetDistForm(CCForm):
    
    KEYWORDS = {
        'en': ['bd'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):

        #Check if tokens are less than 2 at least one person shd be house hold
        try:
            bnr = BedNetReport.objects.get(encounter=self.encounter)
            i = bnr.sleeping_sites
            raise ParseError(_(u"Not enough %(info)s expected: number of " \
                                "sleeping sites and number of bednets" % {'info': i}))   
        except BedNetReport.DoesNotExist:
            raise ParseError(_(u"Assesment not done  for patient yet"))           

