#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

from datetime import datetime
from rapidsms.webui import settings
import reversion
from django.db import models
from django.utils.translation import ugettext as _
from reversion.models import Version
from django.db.models import Q

from mgvmrs.forms import OpenMRSTransmissionError, OpenMRSConsultationForm, \
                         OpenMRSHouseholdForm
from mgvmrs.utils import transmit_form

from childcount.models import CHW, Patient, Encounter
from childcount.models.reports import CCReport

def send_to_omrs(router, *args, **kwargs):

    dt = datetime.now()

    print settings.RAPIDSMS_APPS

    #conf = settings.RAPIDSMS_APPS['mgvmrs']
    individual_id = 2#int(conf['individual_id'])
    household_id = 3#int(conf['household_id'])
    location_id = 2

    print "send"

    encounters = Encounter.objects.filter(Q(sync_omrs__isnull=True) | \
                                          Q(sync_omrs__in=(None, False)))
    print encounters
    for encounter in encounters:
        print "encounter: %s" % encounter
        reports = CCReport.objects.filter(encounter=encounter)

        #is the patient registered? if there are reports it is probably not
        #a new registration. is this really true?
        create = True
        if reports.count():
            create = False
        omrsformclass = None
        if encounter.type == Encounter.TYPE_HOUSEHOLD:
            omrsformclass = OpenMRSHouseholdForm
            form_id = 3
        else:
            omrsformclass = OpenMRSConsultationForm
            form_id = 2
        omrsform = omrsformclass(create, encounter.patient.health_id, \
                                    int(location_id),
                                    int(2),
                                    encounter.encounter_date, \
                                    encounter.patient.dob, \
                                    bool(encounter.patient.estimated_dob), \
                                    encounter.patient.last_name, \
                                    encounter.patient.first_name, '', \
                                    encounter.patient.gender)
        omrsform.openmrs__form_id = form_id
                
        for report in reports:
            omrsdict = report.get_omrs_dict()
            for key in omrsdict:
                value = omrsdict[key]
                omrsform.assign(key, value)

        

        try:
            transmit_form(omrsform)
            encounter.sync_omrs = True
            encounter.save()
        except OpenMRSTransmissionError, e:
            #TODO : Log this error
            print e
            encounter.sync_omrs = False
            encounter.save()
            continue
