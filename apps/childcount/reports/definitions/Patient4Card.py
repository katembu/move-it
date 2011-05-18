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
from childcount.reports.definitions import patients_toolbox as tb

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

            table = tb._create_patient_table()

            for patient_dict in patients:
                patient = Patient.objects\
                                      .get(health_id=patient_dict['health_id'])
                tb._add_patient_to_table(table, patient)

            doc.add_element(table)

        return render_doc_to_file(filepath, rformat, doc)
