#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: tief

from datetime import date

from django.utils.translation import gettext as _
from django.db.models import Count

from ccdoc import Document, Table, Text, Section

from childcount.models import Patient
from locations.models import Location

from childcount.reports.utils import render_doc_to_file
from childcount.reports.report_framework import PrintedReport

class Report(PrintedReport):
    """ list all patients registered on the dashboard """
    title = 'ID ASSIGNEMENT SHEET'
    filename = 'Patient4Card'
    formats = ['html', 'pdf', 'xls']
    argvs = []

    def generate(self, rformat, title, filepath, data):
        doc = Document(title)
        locations = Location.objects.all()
        for location in locations:

            patients = Patient.objects.filter(location=location)\
                                      .values('health_id', 'household')\
                                      .annotate(dcount=Count('household'))

            if patients.count() == 0:
                continue

            #doc.add_element(Section(location.__unicode__()))

            table = self._create_patient_table()

            for patient_dict in patients:
                patient = Patient.objects\
                                      .get(health_id=patient_dict['health_id'])
                self._add_patient_to_table(table, patient)

            doc.add_element(table)

        return render_doc_to_file(filepath, rformat, doc)

    def _create_patient_table(self):
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

    def _add_patient_to_table(self, table, patient):
        """ add patient to table """
        is_bold = patient.is_head_of_household()

        try:
            hh = patient.household.health_id.upper()
        except:
            hh = u""

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
