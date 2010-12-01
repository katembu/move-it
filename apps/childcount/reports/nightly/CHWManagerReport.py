#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

import xlwt
from xlwt import XFStyle, Borders, Font, Style

from django.utils.translation import gettext as _
from django.template import Template, Context

from childcount.models.ccreports import MonthlyCHWReport

from childcount.reports.utils import render_doc_to_file
from childcount.reports.indicator import Indicator
from childcount.reports.report_framework import PrintedReport

class Report(PrintedReport):
    _safe_template = Template('{{value}}')
    _WIDTH_SKINNY = 0x0800

    title = _(u"CHW Manager Report")
    filename = 'chw_manager_report'
    formats = ['xls']

    def _setup_styles(self):
        borders = Borders()
        borders.left = 20
        borders.right = 20
        self._spacer = XFStyle()
        self._spacer.borders = borders

        borders2 = Borders()
        borders2.right = 20
        self._end_section = XFStyle()
        self._end_section.borders = borders2

        borders3 = Borders()
        borders3.bottom = 20
        borders3.right = 20
        self._top_row = XFStyle()
        self._top_row.alignment.horz = 2
        self._top_row.borders = borders3

        fnt = Font()
        fnt.height = 0x100
        self._title_style = XFStyle()
        self._title_style.font = fnt
        self._title_style.borders = borders3

    def generate(self, rformat, title, filepath, data):
        self._setup_styles()

        wb = xlwt.Workbook()
        self._ws = wb.add_sheet(_(u"Report"))
        
        chws = MonthlyCHWReport\
            .objects\
            .filter(is_active=True)\
            .exclude(clinic__isnull=True)\
            .order_by('clinic__name','first_name')

        self._write_merge(0, 0, 0, 1, self.title, \
            self._title_style)
        self._ws.row(0).height = 0x180
        self._print_names(chws)
        self._print_header(chws[0].report_rows())

        for (i,chw) in enumerate(chws):
            self._print_data(i+2, chw)

        wb.save(filepath)

    def _print_data(self, row, chw):
        data = chw.report_rows()
        col = 3
        for metric in data:
            if metric == Indicator.EMPTY:
                col += 1
                continue
            
            ind = Indicator(*metric)
            for i in xrange(0,4):
                self._write(row, col, ind.for_week(i))
                col += 1

            self._write(row, col, ind.for_month(), self._end_section)
            col += 1

    def _add_spacer(self, col):
        self._ws.col(col).width = 0x0100
        self._ws.col(col).set_style(self._spacer)

    def _print_header(self, rows):
        col = 3
        for r in rows:
            if r == Indicator.EMPTY:
                self._add_spacer(col)
                col += 1
                continue

            self._write_merge(0, 0, col, col+4, r[0], \
                self._top_row)
            for j in xrange(0, 4):
                self._ws.col(col+j).width = self._WIDTH_SKINNY
                self._write(1, col+j, \
                    _("W%(week)d") % {'week': j+1})

            self._write(1, col+4, _(u"M"), self._end_section)
            self._ws.col(col+4).set_style(self._end_section)
            self._ws.col(col+4).width = self._WIDTH_SKINNY
            col += 5

    def _print_names(self, chws):
        self._write(1, 0, _(u"CHW Name"))
        self._write(1, 1, _(u"Clinic"))

        for (i, chw) in enumerate(chws):
            self._write(i+2,0, chw.full_name())
            self._write(i+2,1, chw.clinic.code[0:2] if \
                chw.clinic else '--')

        self._ws.col(0).width = 0x1800
        self._ws.col(1).width = self._WIDTH_SKINNY
        self._add_spacer(2)

    def _write(self, r, c, text, style=Style.default_style):
        return self._ws.write(r, c, text, style)

    def _safe_value(self, text):
        return self._safe_template.render(\
            Context({'value': text}))

    def _write_merge(self, r1, r2, c1, c2, text, \
            style=Style.default_style):
        self._ws.write_merge(r1, r2, c1, c2, \
            self._safe_value(text), style)
        
