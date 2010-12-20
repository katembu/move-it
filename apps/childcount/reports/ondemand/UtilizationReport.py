#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: alou


from datetime import date

from django.utils.translation import gettext_lazy as _

from ccdoc import Document, Table, Paragraph, Text, Section

from logger_ng.models import LoggedMessage

from childcount.reports.utils import render_doc_to_file
from childcount.reports.report_framework import PrintedReport


def _(text):
    """ short circuits the translation as not supported by CCdoc
    """
    return text


class Report(PrintedReport):
    """
    """
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
            #~ header_row += [
            #~ Text(_(u'Total')),
            #~ Text(_(u'Average')),
            #~ Text(_(u'Median'))
            #~ ]
        table = Table(header_row.__len__())
        table.add_header_row(header_row)

        doc.add_element(table)

        list_ = list_sms = []

        list_sms.append("Days since last SMS")
        for i in range(1,13):
            ms = LoggedMessage.incoming.filter(date__month=i)
            try:
                lastsms = ms.order_by("-date")[1]
                ldate = "%d-%d-%d"% (lastsms.date.year,\
                                           lastsms.date.month,\
                                            lastsms.date.day)
            except:
                ldate = "none"
            list_.append(ldate)
        list_sms = [Text(sms) for sms in list_]

        table.add_row(list_sms)
        return render_doc_to_file(filepath, rformat, doc)
