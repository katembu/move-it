#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

from datetime import datetime

import rapidsms

from mgvmrs.forms import *
from mgvmrs.utils import *


class App (rapidsms.app.App):
    ''' demo App only

    demonstrates how to use the OMRS link '''

    def handle(self, message):
        # debug only.
        if message.text.startswith('omrs'):
            dt = datetime.now()
            infos = message.text.split(" ")
            mri = infos[1]

            form = OpenMRSOverFiveForm(create=False, mri=mri, location=2, \
                            provider=1, encounter_datetime=dt)

            form.assign('visit_to_health_facility_since_last_home_visit', \
                        form.NO)
            form.assign('danger_signs_present', form.YES)
            form.assign('month_of_current_gestation', 2)
            form.assign('fever', form.YES)
            form.assign('antenatal_visit_number', 4)
            form.assign('number_of_health_facility_visits_since_birth', 7)
            form.assign('tests_ordered', form.TEST_ORDER_MALARIA)
            form.assign('current_medication_order', \
                        (form.MEDIC_ORDER_ANTIBIOTIC, form.MEDIC_ORDER_ORS))
            form.assign('referral_priority', form.REFERRAL_URGENT)
            form.assign('reasons_for_referral__regimen_failure', True)
            form.assign('reasons_for_referral__convulsions', True)
            form.assign('reasons_for_referral__abnormal_vaginal_bleeding', \
                        False)

            #print form.render()
            transmit_form(form)
            message.respond("Form transmitted to OMRS.")

            form2 = OpenMRSUnderFiveForm(create=False, mri=mri, location=2, \
                            provider=1, encounter_datetime=dt)

            form2.assign('visit_to_health_facility_since_last_home_visit', \
                         form2.NO)
            form2.assign('danger_signs_present', form2.YES)
            form2.assign('breastfed_exclusively', form2.YES)
            form2.assign('number_of_health_facility_visits_since_birth', 0)
            form2.assign('fever', form2.YES)
            form2.assign('diarrhea', form2.YES)
            form2.assign('mid_upper_arm_circumference', 46)
            form2.assign('oedema', form2.YES)
            form2.assign('tests_ordered', form2.TEST_ORDER_NONE)
            form2.assign('current_medication_order', \
                       (form2.MEDIC_ORDER_ANTIMALARIAL, form.MEDIC_ORDER_ZINC))
            form2.assign('referral_priority', form2.REFERRAL_WHEN_CONVENIENT)

            transmit_form(form2)

            message.respond("Form transmitted to OMRS.")
