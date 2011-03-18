#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: tief

from datetime import date

from django.utils.translation import gettext as _
from django.db.models import Count

from ccdoc import Document, Table, Text, Section

from childcount.models import Patient, CHW
from locations.models import Location

from childcount.reports.utils import render_doc_to_file
from childcount.reports.report_framework import PrintedReport

class Report(PrintedReport):
    """ list all patients registered on the dashboard """
    title = _(u"Registered Patients")
    filename = 'RegisteredPatient'
    formats = ['html', 'pdf', 'xls']
    argvs = []

    def generate(self, rformat, title, filepath, data):

        doc = Document(title, landscape=True, stick_sections=True)

        chews = CHW.objects.all()
        for chw in chews:

            patients = Patient.objects.filter(chw=chw)\
                                      .order_by('household', 'id')
            if patients.count() == 0:
                continue

            doc.add_element(Section(chw.__unicode__()))
            table = self._create_patient_table()

            for patient in patients:
                self._add_patient_to_table(table, patient)
            
            doc.add_element(table)

        return render_doc_to_file(filepath, rformat, doc)

    def _create_patient_table(self):
        table = Table(8)
        table.add_header_row([
            Text(_(u'HID')),
            Text(_(u'HoHH')),
            Text(_(u'Last name')),
            Text(_(u'First name')),
            Text(_(u'Village')),
            Text(_(u'CHW')),
            Text(_(u'Age')),
            Text(_(u'Gender'))
            ]) 
        # column alignments
        table.set_alignment(Table.ALIGN_LEFT, column=0)
        table.set_alignment(Table.ALIGN_LEFT, column=1)
        table.set_alignment(Table.ALIGN_LEFT, column=2)
        table.set_alignment(Table.ALIGN_LEFT, column=3)
        table.set_alignment(Table.ALIGN_LEFT, column=4)
        table.set_alignment(Table.ALIGN_LEFT, column=5)
        # column sizings
        table.set_column_width(6, column=0)
        table.set_column_width(6, column=1)
        table.set_column_width(5, column=4)
        table.set_column_width(4, column=6)
        table.set_column_width(4, column=7)

        return table

    def _add_patient_to_table(self, table, patient):
        """ add patient to table """
        is_bold = patient.is_head_of_household()
        try:
            hh = patient.household.health_id.upper()
        except:
            hh = u""

        table.add_row([
            Text(patient.health_id.upper(), bold=is_bold),
            Text(hh, bold=is_bold),
            Text(patient.last_name, bold=is_bold),
            Text(patient.first_name, bold=is_bold),
            Text(patient.location.code.upper(), bold=is_bold),
            Text(patient.chw.__unicode__(), bold=is_bold),
            Text(patient.humanised_age(), bold=is_bold),
            Text(patient.gender, bold=is_bold)])
