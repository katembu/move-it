#!/usr/bin/env python
# -*- coding: utf-8 -*-
#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8


from datetime import date

from django.utils.translation import gettext_lazy as _

from ccdoc import Document, Table, Paragraph, Text, Section

from childcount.models import Patient

from childcount.reports.utils import render_doc_to_file
from childcount.reports.report_framework import PrintedReport

def _(text):
    """ short circuits the translation as not supported by CCdoc
    """
    return text

def list_average(values):
    total = 0
    for value in values:
        total += value
    return int(total / values.__len__())

def list_median(values):
    sorted = values
    sorted.sort()
    num = sorted.__len__()
    if num % 2 == 0:
        half = num/2
        center = sorted[num/2:(num/2)+2]
        moy = list_average(center)
    else:
        moy = sorted[num+1/2]
    return moy

class Report(PrintedReport):
    title = 'Utilization Report'
    filename = 'UtilizationReport'
    formats = ['html', 'pdf', 'xls']
    argvs = []

    def generate(self, rformat, title, filepath, data):

        doc = Document(title)

        header_row = [Text(_(u'Indicator:'))]
        for month_num in range(1,13):
            month = date(year=2010, month=month_num, day=1).strftime("%B")
            header_row.append(Text(month.title()))

        header_row += [
            Text(_(u'Total')),
            Text(_(u'Average')),
            Text(_(u'Median'))
        ]

        table = Table(header_row.__len__())
        table.add_header_row(header_row)

        doc.add_element(table)

        # NUMBER of Patient registered PER MONTH
        list_patient = []
        list_patient.append("patient per month")

        list_patient_month = []
        for month_num in range(1,13):
            patient_month = Patient.objects.filter(created_on__month = month_num)
            list_patient_month.append(patient_month.count())

        list_patient += list_patient_month

        total = Patient.objects.all().count()
        list_patient.append(total)

        average = list_average(list_patient_month)
        list_patient.append(average)

        median = list_median(list_patient_month)
        list_patient.append(median)

        list_patient_text= [Text(patient) for patient in list_patient]
        table.add_row(list_patient_text)
        return render_doc_to_file(filepath, rformat, doc)

