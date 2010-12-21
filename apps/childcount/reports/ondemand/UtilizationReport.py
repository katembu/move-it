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
    """ Returns the average of a list """
    total = 0
    for value in values:
        total += value
    return int(total / values.__len__())

def date_under_five():
    """ Returns the date reduced by five years """
    today = date.today()
    date_under_five = date(today.year - 5, today.month, today.day)
    return date_under_five


def list_median(values):
    """ Returns the median of a list """
    sorted_values = values
    sorted_values.sort()
    num = sorted_values.__len__()
    if num % 2 == 0:
        half = num / 2
        center = sorted_values[num / 2: (num / 2) + 2]
        avg = list_average(center)
    else:
        avg = sorted_values[num + 1 / 2]
    return avg


class Report(PrintedReport):
    title = 'Utilization Report'
    filename = 'UtilizationReport'
    formats = ['html', 'pdf', 'xls']
    argvs = []

    def month_nums(self):
        return range(1, 13)

    def generate(self, rformat, title, filepath, data):

        """ Display sms number per month, total, average, median

            Days since last SMS
            NUMBER of Patient registered PER MONTH """

        doc = Document(title)

        header_row = [Text(_(u'Indicator:'))]

        year_today = date.today().year
        for month_num in self.month_nums():
            month = date(year=year_today, month=month_num,\
                                                day=1).strftime("%b")
            header_row.append(Text(month.title()))

        header_row += [
            Text(_(u'Total')),
            Text(_(u'Average')),
            Text(_(u'Median'))
        ]

        self.table = Table(header_row.__len__())
        self.table.add_header_row(header_row)

        # Date at which people are more than 5 years old
        self.date_five = date_under_five()

        # SMS number per month
        self._add_sms_number_per_month_row()

        # NUMBER of Patient registered PER MONTH
        self._add_number_patient_reg_month()

        # Days since last SMS
        self._add_days_since_last_sms_month()

        # Adult Women registered
        self._add_adult_registered('F')

        # Adult Men registered
        self._add_adult_registered('M')

        doc.add_element(self.table)

        return render_doc_to_file(filepath, rformat, doc)

    def _add_sms_number_per_month_row(self):
        """ SMS number per month """

        list_sms = []
        list_sms_month = []

        list_sms.append("SMS per month")

        for month_num in self.month_nums():
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
        self.table.add_row(list_sms_text)

    def _add_number_patient_reg_month(self):
        list_patient = []
        list_patient.append("patient per month")

        list_patient_month = []
        for month_num in self.month_nums():
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
        self.table.add_row(list_patient_text)

    def _add_days_since_last_sms_month(self):
        list_date = list_sms = []

        list_sms.append("Days since last SMS")
        for i in self.month_nums():
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
        self.table.add_row(list_sms)

    def _add_adult_registered(self, gender):
        """ Adult registered

            Params:
                * gender """

        list_adult = []
        list_adult_month = []

        if gender == 'M':
            list_adult.append("Men per month")
        elif gender == 'F':
            list_adult.append("Women per month")

        for month_num in self.month_nums():
            adult_month = Patient.objects.filter(gender=gender,
                                            created_on__month=month_num,
                                            dob__lt=self.date_five)
            list_adult_month.append(adult_month.count())

        list_adult += list_adult_month

        total = Patient.objects.filter(dob__lt=self.date_five,
                                       gender=gender).count()
        list_adult.append(total)

        average = list_average(list_adult_month)
        list_adult.append(average)

        median = list_median(list_adult_month)
        list_adult.append(median)

        list_adult_text = [Text(adult) for adult in list_adult]
        self.table.add_row(list_adult_text)

