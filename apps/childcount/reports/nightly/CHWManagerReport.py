#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

import xlwt
from xlwt import XFStyle, Borders, Font, Style

from django.utils.translation import gettext as _
from django.template import Template, Context

from childcount.models.ccreports import MonthlyCHWReport
from childcount.models import Clinic

from childcount.reports.utils import render_doc_to_file
from childcount.reports.utils import MonthlyPeriodSet
from childcount.reports.utils import QuarterlyPeriodSet
from childcount.reports.utils import AnnualPeriodSet

from childcount.reports.indicator import Indicator, INDICATOR_EMPTY
from childcount.reports.report_framework import PrintedReport

class Report(PrintedReport):
    title = _(u"CHW Manager Report: ")
    filename = 'chw_manager_report_'
    formats = ['xls']
    variants = [
        (u"Monthly", 'monthly', \
            {'period_cls': MonthlyPeriodSet}),
        (u"Quarterly", 'quarterly', \
            {'period_cls': QuarterlyPeriodSet}),
        (u"Annual", 'annual', \
            {'period_cls': AnnualPeriodSet}),
    ]

    _safe_template = Template('{{value}}')
    _WIDTH_SKINNY = 0x0800

    _aggregate_on = []
    
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
        
        self._end_section_perc = XFStyle()
        self._end_section_perc.borders = borders2
        self._end_section_perc.num_format_str = '0.0%'

        borders3 = Borders()
        borders3.bottom = 20
        borders3.right = 20
        bfont = Font()
        bfont.bold = True
        self._top_row = XFStyle()
        self._top_row.font = bfont
        self._top_row.alignment.horz = 2
        self._top_row.borders = borders3

        fnt = Font()
        fnt.height = 0x100
        fnt.bold = True
        self._title_style = XFStyle()
        self._title_style.font = fnt
        self._title_style.borders = borders3

        self._perc_style = XFStyle()
        self._perc_style.num_format_str = '0.0%'

        tbbords = Borders()
        tbbords.top = 30
        tbbords.bottom = 30
        self._total_style = XFStyle()
        self._total_style.borders = tbbords
        self._total_style.font = bfont
        self._total_style.alignment.horz = 3

        self._total_perc_style = XFStyle()
        self._total_perc_style.borders = tbbords
        self._total_perc_style.font = bfont
        self._total_perc_style.num_format_str = '0.0%'

    def generate(self, rformat, title, filepath, data):
        self.per_cls = data['period_cls']

        self._setup_styles()

        wb = xlwt.Workbook()
        self._ws = wb.add_sheet(_(u"Report"))
        
        chws = MonthlyCHWReport\
            .objects\
            .filter(is_active=True)\
            .exclude(clinic__isnull=True)\
            .order_by('clinic__name','first_name')

        # Set up data structures for column totals
        self._aggregate_on = []
        seen = []

        for chw in chws:
            if chw.clinic.pk in seen:
                continue
            else:
                seen.append(chw.clinic.pk)

            self._aggregate_on.append((unicode(chw.clinic) + u": ", \
                [chw.clinic.pk]))

        self._aggregate_on.append((_(u"Millennium Village: "), seen))
        self._indicator_data = [[] for agg in self._aggregate_on]

        # Write report titles
        self._write_merge(0, 0, 0, 1, self.title, self._title_style)
        self._write_merge(1, 1, 0, 1, \
            self.per_cls.period_start_date(0).strftime('%d-%b-%Y') + \
                _(u" through ") + \
            self.per_cls.period_end_date(\
                self.per_cls.num_periods).strftime('%d-%b-%Y'))

        self._ws.row(0).height = 0x180
        self._print_names(chws)

        header_rows = chws[0].report_indicators()
        self._print_header(header_rows)

        row = 4
        for (i,chw) in enumerate(chws):
            self._print_data(row, chw)
            row += 1
        row += 1
        self._print_totals(row, header_rows)

        wb.save(filepath)

    def _print_totals(self, row, header_rows):
        for (num, (title, _)) in enumerate(self._aggregate_on):
            i = 0
            col = 3

            self._write_merge(row+num, row+num, 0, 1, title,\
                self._total_style)

            for ind in header_rows:
                if ind == INDICATOR_EMPTY:
                    self._add_spacer(col)
                    col += 1
                    continue

                for j in xrange(0, self.per_cls.num_periods+1):
                    self._write(row+num, col, \
                        ind.aggregate_col(self._indicator_data[num][i]), \
                        self._total_perc_style if \
                            ind.is_percentage else self._total_style)
                    i += 1
                    col += 1
            
    def _print_data(self, row, chw):
        data = chw.report_indicators()
        col = 3
        j = 0   # Index into _indicator_data cache
        for ind in data:
            if ind == INDICATOR_EMPTY:
                col += 1
                continue
           
            for i in xrange(0, self.per_cls.num_periods):
                self._aggregate_data(chw, \
                    ind.for_period_raw(self.per_cls, i), \
                    j)

                j += 1

                self._write(row, \
                    col, \
                    ind.for_period(self.per_cls, i),\
                    self._perc_style if ind.is_percentage else Style.default_style)
                col += 1

            self._aggregate_data(chw, ind.for_total_raw(self.per_cls), j)
            #print ">%s" % unicode(ind.for_total_raw(self.per_cls))
            j += 1
            self._write(row,\
                col,\
                ind.for_total(self.per_cls),\
                self._end_section_perc if ind.is_percentage else self._end_section)
            col += 1

    def _aggregate_data(self, chw, bit, index):
        for (num, (name, lst)) in enumerate(self._aggregate_on):
            if chw.clinic.pk in lst:
                #print '_indicator_data[%d][%d] = \
                # %s' % (num, index, unicode(bit))

                self._indicator_data[num][index].append(bit)

    def _add_spacer(self, col):
        self._ws.col(col).width = 0x0100
        self._ws.col(col).set_style(self._spacer)

    def _print_header(self, indicators):
        col = 3
        LABEL_ROW = 2
        DATE_ROW = 3
        n_indicators = 0
        for ind in indicators:
            if ind == INDICATOR_EMPTY:
                self._add_spacer(col)
                col += 1
                continue

            n_indicators += 1

            self._write_merge(LABEL_ROW, \
                LABEL_ROW, col, col+self.per_cls.num_periods, \
                ind.title, self._top_row)

            for j in xrange(0, self.per_cls.num_periods):
                n_indicators += 1
                self._ws.col(col).width = self._WIDTH_SKINNY
                self._write(DATE_ROW, col, self.per_cls.period_name(j))
                col += 1

            self._write(DATE_ROW, 
                col, 
                self.per_cls.total_name,
                self._end_section)

            self._ws.col(col).set_style(self._end_section)
            self._ws.col(col).width = self._WIDTH_SKINNY
            col += 1

        # For every aggregation set
        for i in xrange(0, len(self._aggregate_on)):
            # and for every indicator to be tracked
            for j in xrange(0, n_indicators):
                # add an empty list to store data
                self._indicator_data[i].append([])
                
    def _print_names(self, chws):
        self._write(2, 0, _(u"CHW Name"), self._top_row)
        self._write(2, 1, _(u"Clinic"), self._top_row)

        for (i, chw) in enumerate(chws):
            self._write(i+4,0, chw.full_name())
            self._write(i+4,1, chw.clinic.code[0:2] if \
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
        
