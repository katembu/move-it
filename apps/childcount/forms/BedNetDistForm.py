#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from django.utils.translation import ugettext as _
from django.db.models import Sum

from childcount.forms import CCForm
from childcount.models.reports import BednetReport, BednetUtilization, BednetIssuedReport
from childcount.models import Patient, Encounter
from childcount.utils import DOBProcessor
from childcount.exceptions import ParseError, BadValue, Inapplicable
from childcount.forms.utils import MultipleChoiceField


class SBedNetForm(CCForm):
    KEYWORDS = {
        'en': ['bc'],
        'fr': ['bc'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):
        if len(self.params) < 3:
            raise ParseError(_(u"Not enough info. Expected: number of " \
                                "sleeping sites and number of bednets."))

        try:
            bnr = BednetReport.objects.get(encounter=self.encounter)
        except BednetReport.DoesNotExist:
            bnr = BednetReport(encounter=self.encounter)
            overwrite = False
        else:
            bnr.reset()
            overwrite = True

        bnr.form_group = self.form_group

        if not self.params[1].isdigit():
            raise ParseError(_(u"Number of sleeping sites must be entered as" \
                                "a number."))

        bnr.sleeping_sites = int(self.params[1])

        if not self.params[2].isdigit():
            raise ParseError(_(u"Number of bednets must be a " \
                                "number"))

        bnr.nets = int(self.params[2])

        bnr.save()

        self.response = _(u"%(sites)d sleeping site(s), %(nets)d bednet(s)") %\
                           {'sites': bnr.sleeping_sites, 'nets': bnr.nets}

'''Bed Net Distribution '''


class BedNetDistForm(CCForm):
    KEYWORDS = {
        'en': ['bnd'],
        'fr': ['bnd'],
        }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):
        #check if house hold survey has been taken
        try:
            bnr = BednetReport.objects.get(encounter__patient=self.\
                                        encounter.patient)
        except BednetReport.DoesNotExist:
            raise ParseError(_(u"Report  Survey doesnt exist for Kamau"))
        
        else:
            ssite = bnr.sleeping_sites
            active_bdnet = bnr.nets
            bdnt_needed =  ssite - active_bdnet

        #create object
        try:
            pr = BednetIssuedReport.objects.get(encounter=self.encounter)
            pr.reset()
        except BednetIssuedReport.DoesNotExist:
            pr = BednetIssuedReport(encounter=self.encounter)

        pr.form_group = self.form_group

        #check bednet issued to date
        bdnt_issued = BednetIssuedReport.objects.filter(encounter__patient\
                                    =self.encounter.patient).aggregate(\
                                    stotal=Sum('bednet_received'))['stotal']
        if bdnt_issued is None:
            bdnt_issued = 0  

        #calculate bednet required to be issued
        bdnt_required = bdnt_needed - bdnt_issued
        #if less then zero nno bed ned required
        if bdnt_required < 0:
            self.response = _(u"%(patient)s .Has already received " \
                                    "%(nets)d for sleeping %(site)d " \
                                    "sites.  ") % \
                                    {'patient': patient, 'nets': bdnt_needed, \
                                     'site': bdnt_needed}
        else:
            self.response = _(u"%(patient)s. %(ssite)d Sleeping sites. " \
                                    "Need %(bdnt_required)d bednet(s).Last " \
                                    "received: ") % \
                                    {'patient': patient, 'ssite': bdnt_needed, \
                                     'bdnt_required': bdnt_required}

        pr.bednet_received = bdnt_required
        pr.save()


''' BED NET UTILIZATION FORM '''


class SBedNetUtilForm(CCForm):
    KEYWORDS = {
        'en': ['bu'],
        'fr': ['bu'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):
        if len(self.params) < 3:
            raise ParseError(_(u"Not enough info. Expected: number of " \
                                "children who slept here last nite | "\
                                " how many slept under of bednets."))

        try:
            bnut_rpt = BednetUtilization.objects.get(encounter=self.encounter)
            bnut_rpt.reset()
        except BednetUtilization.DoesNotExist:
            bnut_rpt = BednetUtilization(encounter=self.encounter)

        bnut_rpt.form_group = self.form_group
        if not self.params[1].isdigit():
            raise ParseError(_(u"Number of children who slept here last" \
                                "nite should be number"))

        bnut_rpt.child_underfive = int(self.params[1])
        if not self.params[2].isdigit():
            raise ParseError(_(u"Number of children under bednet should " \
                                "be number "))

        bnut_rpt.child_lastnite = int(self.params[2])
        if bnut_rpt.child_lastnite > bnut_rpt.child_underfive:
            raise ParseError(_(u"Number of children who slept under bednet " \
                                " should be more than who slept here"))

        bnut_rpt.save()

        self.response = _(u"%(sites)d child(ren) slept here last nite " \
                           " %(nets)d slept under bednet(s)") %\
                           {'sites': bnut_rpt.child_underfive, \
                            'nets': bnut_rpt.child_lastnite}


class Bednetlookup(CCForm):
    KEYWORDS = {
        'en': ['bs'],
        'fr': ['bs'],
        }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):
        #check if survey has been done
        try:
            bnr = BednetReport.objects.get(encounter__patient=self.\
                                        encounter.patient)
        except BednetReport.DoesNotExist:
            raise ParseError(_(u"Report  Survey doesnt exist for Kamau"))

        else:
            ssite = int(bnr.sleeping_sites)
            active_bdnet = int(bnr.nets)
            bdnt_needed = ssite - active_bdnet 
            #check bednet issued to date
            bdnt_issued = BednetIssuedReport.objects.filter(encounter__patient \
                                    =self.encounter.patient).aggregate(stotal=\
                                    Sum('bednet_received'))['stotal']
            if bdnt_issued is None:
                bdnt_issued = 0  

            #calculate bednet required to be issued
            bdnt_required = bdnt_needed - bdnt_issued

            if bdnt_required <= 0:
                self.response = _(u"%(patient)s has already %(nets)d bednets " \
                                  "for %(site)d .Last received from ") % \
                                    {'patient': patient, 'nets': bdnt_needed, \
                                     'site': bdnt_needed}

            else:
                self.response = _(u"%(patient)s. Need %(nets)d bednets " \
                                  "for %(site)d sites.Last received from ") % \
                                    {'patient': patient, 'nets': bdnt_needed, \
                                     'site': bdnt_needed}

''' BEDNET ISSUED +BD incase no enough bednets '''


class BednetIssuedForm(CCForm):
    KEYWORDS = {
        'en': ['bd'],
        'fr': ['bd'],
    }
    ENCOUNTER_TYPE = Encounter.TYPE_HOUSEHOLD

    def process(self, patient):
        
