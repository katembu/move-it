#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

from rapidsms.webui import settings
from django.db.models import Q
from mgvmrs.forms import OpenMRSTransmissionError, OpenMRSConsultationForm, \
                         OpenMRSHouseholdForm
from mgvmrs.utils import transmit_form

from childcount.models import Encounter
from childcount.models.reports import CCReport

def send_to_omrs(router, *args, **kwargs):
    ''' Forwards Encounter to OpenMRS

    Scheduler callback.

    Fetchs all non-synced Encounter
    Send each to OpenMRS via HTTP '''

    # retrieve mgvmrs configuration
    conf = settings.RAPIDSMS_APPS['mgvmrs']

    # Form IDs and Field location ID are site-specific
    individual_id = int(conf['individual_id'])
    household_id = int(conf['household_id'])
    location_id = int(conf['location_id'])

    # provider is temporary fixed.
    # TODO: add field to CHW to store OMRS ID
    provider_id = 1

    # request all non-synced Encounter
    encounters = Encounter.objects.filter(Q(sync_omrs__isnull=True) | \
                                          Q(sync_omrs__in=(None, False)))

    for encounter in encounters:
        # reports contains actual data for an encounter.
        reports = CCReport.objects.filter(encounter=encounter)

        #is the patient registered? if there are reports it is probably not
        #a new registration. is this really true?
        create = True
        if reports.count():
            create = False

        # select OpenMRS Xform according to Encounter type
        omrsformclass = None
        if encounter.type == Encounter.TYPE_HOUSEHOLD:
            omrsformclass = OpenMRSHouseholdForm
            form_id = household_id
        else:
            omrsformclass = OpenMRSConsultationForm
            form_id = individual_id

        # create form
        omrsform = omrsformclass(create, encounter.patient.health_id, \
                                    int(location_id),
                                    int(provider_id),
                                    encounter.encounter_date, \
                                    encounter.patient.dob, \
                                    bool(encounter.patient.estimated_dob), \
                                    encounter.patient.last_name, \
                                    encounter.patient.first_name, '', \
                                    encounter.patient.gender)
        # assign site-specific ID
        omrsform.openmrs__form_id = form_id

        # each report contains reference to OMRS fields
        for report in reports:
            omrsdict = report.get_omrs_dict()
            for key in omrsdict:
                value = omrsdict[key]
                omrsform.assign(key, value)      

        # send xform to omrs and change sync status
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
