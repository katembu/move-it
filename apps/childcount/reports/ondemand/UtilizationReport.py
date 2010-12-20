#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: tief

from datetime import date

from django.utils.translation import gettext_lazy as _

from ccdoc import Document, Table, Paragraph, Text, Section

from childcount.models import Patient
from locations.models import Location

from childcount.reports.utils import render_doc_to_file
from childcount.reports.report_framework import PrintedReport


def _(text):
    """ short circuits the translation as not supported by CCdoc
    """
    return text


class Report(PrintedReport):
    """ list all patients registered on the dashboard """
    title = 'Utilization report'
    filename = 'Utilization report'
    formats = ['html', 'pdf', 'xls']
    argvs = []

    def generate(self, rformat, title, filepath, data):
        doc = Document(title)
        doc.add_element(Paragraph(u'list of children under 5 years'))

        table = Table(6)
        table.add_header_row([
            Text(_(u'Health ID')),
            Text(_(u'First name')),
            Text(_(u'Last name')),
            Text(_(u'Location')),
            Text(_(u'Age')),
            Text(_(u'Gender'))
            ])

        patients = Patient.objects.all()

        for patient in patients:
            if patient.years() <= 5:
                self._add_patient_to_table(table, patient)

        doc.add_element(table)
        return render_doc_to_file(filepath, rformat, doc)

    def _add_patient_to_table(self, table, patient):
        """ add patient to table """
        table.add_row([
            Text(patient.health_id),
            Text(patient.last_name),
            Text(patient.first_name),
            Text(patient.location.__unicode__()),
            Text(patient.humanised_age()),
            Text(patient.gender)
            ])
