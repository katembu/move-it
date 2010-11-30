#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

from django.utils.translation import gettext_lazy as _

from ccdoc import Document, Table, Paragraph, Text, Section

from childcount.models import CHW
from childcount.models.reports import HouseholdVisitReport
from childcount.models.reports import FamilyPlanningReport
from childcount.models.ccreports import CHWMonthlyReport

from childcount.reports.utils import render_doc_to_file
from childcount.reports.utils import reporting_week_monday
from childcount.reports.utils import reporting_week_sunday
from childcount.reports.indicator import Indicator
from childcount.reports.report_framework import PrintedReport

class Report(PrintedReport):
    title = 'Monthly CHW Report'
    filename = 'monthly_chw_report'
    formats = ['pdf','xls','html']

    def _reporting_week_date_str(self, week_num):
        return 'Wk of '+reporting_week_monday(week_num)\
            .strftime('%e %b')

    def generate(self, rformat, title, filepath, data):
        doc = Document(title)

        for chw in CHWMonthlyReport.objects.filter(is_active=True, pk=74):
            doc.add_element(Section(chw.full_name())) 
            doc.add_element(Paragraph("For days %(start)s - %(end)s" %\
                {'start': reporting_week_monday(0).strftime('%e %B %Y'),\
                'end': reporting_week_sunday(3).strftime('%e %B %Y')}))

            table = Table(6)
            table.add_header_row([
                Text(u'Indicator'),
                Text(self._reporting_week_date_str(0)),
                Text(self._reporting_week_date_str(1)),
                Text(self._reporting_week_date_str(2)),
                Text(self._reporting_week_date_str(3)),
                Text(u'Tot/Avg'),
            ])

            for row in chw.report_rows():
                ind = Indicator(*row)
                table.add_row(map(Text,[ind.title, ind.for_week(0), ind.for_week(1),
                    ind.for_week(2), ind.for_week(3), ind.for_month()]))

            doc.add_element(table)
        return render_doc_to_file(filepath, rformat, doc)


