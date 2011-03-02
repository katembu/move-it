#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: tief

from django.utils.translation import gettext as _

from ccdoc import Document, Table, Text, Section

from childcount.models import Patient


def _create_patient_table():
    table = Table(7)
    table.add_header_row([
        Text(_(u'HID')),
        Text(_(u'Name')),
        Text(_(u'DOB')),
        Text(_(u'Sex')),
        Text(_(u'Location')),
        Text(_(u'HoHH')),
        Text(_(u'Village'))])
    # column alignments
    table.set_alignment(Table.ALIGN_LEFT, column=0)
    table.set_alignment(Table.ALIGN_LEFT, column=1)
    table.set_alignment(Table.ALIGN_LEFT, column=2)
    table.set_alignment(Table.ALIGN_LEFT, column=3)
    table.set_alignment(Table.ALIGN_LEFT, column=4)
    table.set_alignment(Table.ALIGN_LEFT, column=5)
    table.set_alignment(Table.ALIGN_LEFT, column=6)

    return table

def _add_patient_to_table(table, patient, only_hohh=False):
    """ add patient to table """
    is_bold = is_hohh = patient.is_head_of_household()

    if only_hohh and not is_hohh:
        return

    try:
        hh = patient.household.health_id.upper()
    except:
        hh = u""

    if only_hohh:
        hh = u"%d" % Patient.objects.filter(household=patient).count()

    dob = patient.dob.strftime('%d.%m.%Y')
    if patient.estimated_dob:
        dob = u"%s*" % dob

    location = u"%(village)s/%(code)s-%(chw)s" \
               % {'village': patient.location.name.title(), \
                  'code': patient.location.code.upper(), \
                  'chw': patient.chw.id.__str__().zfill(3)}

    table.add_row([
        Text(patient.health_id.upper(), bold=is_bold),
        Text(patient.full_name(), bold=is_bold),
        Text(dob, bold=is_bold),
        Text(patient.gender, bold=is_bold),
        Text(location, bold=is_bold),
        Text(hh, bold=is_bold),
        Text(patient.location.name.upper(), bold=is_bold)])
