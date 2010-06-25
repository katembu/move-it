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
