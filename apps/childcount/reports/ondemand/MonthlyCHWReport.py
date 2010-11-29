#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

from django.utils.translation import gettext_lazy as _

from ccdoc import Document, Table, Paragraph, Text, Section

from childcount.reports.utils import render_doc_to_file
from childcount.reports.report_framework import PrintedReport
from childcount.models import CHW
from childcount.models.reports import HouseholdVisitReport
from childcount.models.reports import FamilyPlanningReport
from childcount.models.ccreports import CHWMonthlyReport
from childcount.reports.indicator import Indicator

class Report(PrintedReport):
    title = 'Monthly CHW Report'
    filename = 'monthly_chw_report'
    formats = ['pdf','xls','html']

    def generate(self, rformat, title, filepath, data):
        doc = Document(title)

        for chw in CHWMonthlyReport.objects.filter(is_active=True, pk=97):
            doc.add_element(Section(chw.full_name())) 
            doc.add_element(Paragraph("For days START - END"))

            table = Table(6)
            table.add_header_row([
                Text(_(u'Indicator')),
                Text(_(u'W1')),
                Text(_(u'W2')),
                Text(_(u'W3')),
                Text(_(u'W4')),
                Text(_(u'Tot/Avg')),
            ])

            for row in chw.report_rows():
                ind = Indicator(*row)
                table.add_row(map(Text,[ind.title, ind.for_week(0), ind.for_week(1),
                    ind.for_week(2), ind.for_week(3), ind.for_month()]))

            doc.add_element(table)
        return render_doc_to_file(filepath, rformat, doc)


