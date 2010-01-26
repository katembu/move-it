#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

from datetime import datetime

import rapidsms
from mgvmrs.forms.OpenMRSUnderFiveForm import *
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
            bcg = None
            if infos.count('+bcg') > 0:
                bcg = True
            if infos.count('-bcg') > 0:
                bcg = False

            form = OpenMRSUnderFiveForm(create=False, mri=mri, location=2, \
                            provider=1, encounter_datetime=dt)

            if not bcg == None:
                bcgv = form.YES if bcg else form.NO
                form.assign('bacille_camile_guerin_vaccination', bcgv)

            form.assign('current_medication_order', \
                        (form.CURRENT_MEDIC_ORDER_ANTIMALARIAL, \
                         form.CURRENT_MEDIC_ORDER_ANTIBIOTIC))

            form.assign('current_medication_order_1', (form.MEDIC_ORDER_ZINC))

            #print form.render()
            transmit_form(form)

            message.respond("Form transmitted to OMRS.")
