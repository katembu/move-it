#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: tief

import time
from datetime import date

from django.utils.translation import gettext as _
from django.db.models import Count

from ccdoc import Document, Table, Text, Section

from childcount.models import CHW

from reportgen.utils import render_doc_to_file
from reportgen.PrintedReport import PrintedReport

class ReportDefinition(PrintedReport):
    """ list all CHW """
    title = _('CHW List')
    filename = 'CHWList'
    formats = ['html', 'pdf', 'xls']

    def generate(self, time_period, rformat, title, filepath, data):
        doc = Document(title)

        chews = CHW.objects.all().order_by('id', 'first_name', 'last_name')
        table = self._create_chw_table()

        current = 0
        total = chews.count() + 1
        self.set_progress(0)
        for chw in chews:
            time.sleep(5) 
            self._add_chw_to_table(table, chw)
            current += 1
            self.set_progress(100.0*current/total)

        doc.add_element(table)

        rval = render_doc_to_file(filepath, rformat, doc)
        self.set_progress(100)

        return rval

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
       
        l = chw.location or chw.clinic
        if l:
            location = u"%(village)s/%(code)s" \
                       % {'village': l.name.title(),
                          'code': l.code.upper()}
        else:
            location = u"--"

        table.add_row([
            Text(chw.id.__str__().upper()),
            Text(chw.get_full_name()),
            Text(location),
            Text(chw.username),
            Text(chw.language.upper())])
