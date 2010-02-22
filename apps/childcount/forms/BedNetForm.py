#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin


from django.utils.translation import ugettext as _

from childcount.forms import CCForm
from childcount.models.reports import BedNetReport
from childcount.exceptions import ParseError


class BedNetForm(CCForm):
    KEYWORDS = {
        'en': ['bn'],
    }

    def process(self, patient):
        if len(self.params) < 3:
            raise ParseError(_(u"Not enough info, expected: number of " \
                                "bednets and number of sleeping sites"))

        chw = self.message.persistant_connection.reporter.chw

        bnr = BedNetReport(created_by=chw, \
                            patient=patient)

        if not self.params[1].isdigit():
            raise ParseError(_(u"Number of bednets must be a " \
                                "number"))

        bnr.nets = int(self.params[1])

        if not self.params[2].isdigit():
            raise ParseError(_(u"Number of sleeping sites must be a " \
                                "number"))

        bnr.sleeping_sites = int(self.params[2])
        bnr.save()

        self.response = _(u"%(nets)d bednets, %(sites)d sleeping sites") % \
                           {'nets': bnr.nets, 'sites': bnr.sleeping_sites}
