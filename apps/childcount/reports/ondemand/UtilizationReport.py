#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: alou


from datetime import date

from django.utils.translation import gettext_lazy as _

from ccdoc import Document, Table, Paragraph, Text, Section

from logger_ng.models import LoggedMessage

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
        half = num / 2
        center = sorted[num / 2: (num / 2) + 2]
        moy = list_average(center)
    else:
        moy = sorted[num + 1 / 2]
    return moy


class Report(PrintedReport):
    title = 'Utilization Report'
    filename = 'UtilizationReport'
    formats = ['html', 'pdf', 'xls']
    argvs = []

    def generate(self, rformat, title, filepath, data):

        """ Display sms number per month, total, average, median
            Days since last SMS
            NUMBER of Patient registered PER MONTH
        """

        doc = Document(title)

        header_row = [Text(_(u'Indicator:'))]

        for month_num in range(1, 13):
            month = date(year=2010, month=month_num, day=1).strftime("%B")

        year_today = date.today().year
        for month_num in range(1, 13):
            month = date(year=year_today, month=month_num,\
                                                day=1).strftime("%B")
            header_row.append(Text(month.title()))

        header_row += [
            Text(_(u'Total')),
            Text(_(u'Average')),
            Text(_(u'Median'))
        ]

        table = Table(header_row.__len__())
        table.add_header_row(header_row)

        doc.add_element(table)

         # SMS NUMBER PER MONTH
        list_sms = []
        list_sms.append("SMS per month")

        list_sms_month = []
        for month_num in range(1, 13):
            sms_month = LoggedMessage.incoming.filter(date__month=month_num)
            list_sms_month.append(sms_month.count())

        list_sms += list_sms_month

        total = LoggedMessage.incoming.all().count()
        list_sms.append(total)

        average = list_average(list_sms_month)
        list_sms.append(average)

        median = list_median(list_sms_month)
        list_sms.append(median)

        list_sms_text = [Text(sms) for sms in list_sms]
        table.add_row(list_sms_text)

        # NUMBER of Patient registered PER MONTH
        list_patient = []
        list_patient.append("patient per month")

        list_patient_month = []
        for month_num in range(1, 13):
            patient_month = Patient.objects.filter(created_on__month=month_num)
            list_patient_month.append(patient_month.count())

        list_patient += list_patient_month

        total = Patient.objects.all().count()
        list_patient.append(total)

        average = list_average(list_patient_month)
        list_patient.append(average)

        median = list_median(list_patient_month)
        list_patient.append(median)

        list_patient_text = [Text(patient) for patient in list_patient]
        table.add_row(list_patient_text)

        # Days since last SMS
        list_date = list_sms = []

        list_sms.append("Days since last SMS")
        for i in range(1, 13):
            ms = LoggedMessage.incoming.filter(date__month=i)
            try:
                lastsms = ms.order_by("-date")[1]
                ldate = "%d-%d-%d" % (lastsms.date.year,\
                                           lastsms.date.month,\
                                            lastsms.date.day)
            except:
                ldate = "none"
            list_date.append(ldate)
        for i in range(3):
            list_date.append("")

        list_sms = [Text(sms) for sms in list_date]
        table.add_row(list_sms)
        return render_doc_to_file(filepath, rformat, doc)
