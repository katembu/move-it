#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: tief

from datetime import date

from django.utils.translation import gettext as _
from django.db.models import Sum

from ccdoc import Document, Table, Text, Section, Paragraph

from childcount.models import BednetStock, DistributionPoints
from childcount.models import BednetIssuedReport

from childcount.reports.utils import render_doc_to_file
from childcount.reports.report_framework import PrintedReport

class Report(PrintedReport):
    title = 'Bednet Stock Report'
    filename = 'dp'
    formats = ['html', 'xls', 'pdf']

    def generate(self, rformat, title, filepath, data):
        doc = Document(title, landscape=True, stick_sections=True)
        table = self._create_table()
        for bs in  BednetStock.objects.all():
            self._add_stock_to_table(table, bs)
        doc.add_element(table)

        return render_doc_to_file(filepath, rformat, doc)

    def _create_table(self):
        table = Table(5)
        table.add_header_row([
            Text(_(u'Distribution Site')),
            Text(_(u'DIstribution Date')),
            Text(_(u'Start Point')),
            Text(_(u'End Point')),
            Text(_(u'Issued'))
            ])
        # column alignments
        table.set_alignment(Table.ALIGN_LEFT, column=0)
        table.set_alignment(Table.ALIGN_LEFT, column=1)
        table.set_alignment(Table.ALIGN_LEFT, column=2)
        table.set_alignment(Table.ALIGN_LEFT, column=3)
        # column sizings
        table.set_column_width(20, column=0)

        return table

    def _add_stock_to_table(self, table, stock):
        is_bold = False
        table.add_row([
            Text(stock.location.__unicode__(), bold=is_bold),
            Text(stock.created_on.strftime('%d-%b-%Y'), bold=is_bold),
            Text(stock.start_point, bold=is_bold),
            Text(stock.end_point, bold=is_bold),
            Text((stock.start_point - stock.end_point), bold=is_bold)])
