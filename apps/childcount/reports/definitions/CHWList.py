#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: tief

from datetime import date

from django.utils.translation import gettext as _
from django.db.models import Count

from ccdoc import Document, Table, Text, Section

from childcount.models import CHW

from childcount.reports.utils import render_doc_to_file
from childcount.reports.report_framework import PrintedReport

class Report(PrintedReport):
    """ list all CHW """
    title = _(u"CHW List")
    filename = 'CHWList'
    formats = ['html', 'pdf', 'xls']
    argvs = []

    def generate(self, rformat, title, filepath, data):
        doc = Document(title)

        chews = CHW.objects.all().order_by('id', 'first_name', 'last_name')
        table = self._create_chw_table()

        for chw in chews:
            self._add_chw_to_table(table, chw)

        doc.add_element(table)

        return render_doc_to_file(filepath, rformat, doc)

    def _create_chw_table(self):
        table = Table(5)
        table.add_header_row([
            Text(_(u'ID')),
            Text(_(u'Name')),
            Text(_(u'Location')),
            Text(_(u'Username')),
            Text(_(u'Lang'))])

        table.set_column_width(4, 0)
        table.set_column_width(14, 3)
        table.set_column_width(4, 4)

        # column alignments
        table.set_alignment(Table.ALIGN_LEFT, column=0)
        table.set_alignment(Table.ALIGN_LEFT, column=1)
        table.set_alignment(Table.ALIGN_LEFT, column=2)
        table.set_alignment(Table.ALIGN_LEFT, column=3)
        table.set_alignment(Table.ALIGN_CENTER, column=4)

        return table

    def _add_chw_to_table(self, table, chw):
        """ add chw to table """
        
        location = u"%(village)s/%(code)s" \
                   % {'village': chw.location.name.title(), \
                      'code': chw.location.code.upper()}

        table.add_row([
            Text(chw.id.__str__().upper()),
            Text(chw.get_full_name()),
            Text(location),
            Text(chw.username),
            Text(chw.language.upper())])
