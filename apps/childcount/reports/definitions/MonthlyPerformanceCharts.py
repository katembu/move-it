#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import copy
import numpy

from django.utils.translation import gettext_lazy as _

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from reportlab.platypus import Paragraph, SimpleDocTemplate, PageBreak
from reportlab.platypus import Table, TableStyle, NextPageTemplate
from reportlab.platypus.flowables import KeepTogether

from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.charts.legends import Legend

from childcount.models.ccreports import GraphicalClinicReport

from childcount.reports.utils import TwoMonthPeriodSet
from childcount.reports.report_framework import PrintedReport

styles = getSampleStyleSheet()
styleN = styles['Normal']
styleH = styles['Heading1']
styleH3 = styles['Heading2']
styleH3.alignment = 1

class Report(PrintedReport):
    title = _(u'Monthly Performance Charts')
    filename = 'monthly_performance_charts'
    formats = ('pdf',)

    def generate(self, rformat, title, filepath, data):
        
        if rformat != 'pdf':
            raise NotImplementedError(\
                _(u'Can only generate PDF for performance charts'))

        f = open(filepath, 'w')
        story = [Paragraph(unicode(title), styleH)]

        clinics = GraphicalClinicReport.objects.order_by('name')
        # Get indicator sets for each clinic
        c_inds = map(lambda c: c.indicators(), clinics)

        table_data = [[]]

        # data[t][c] should be the value at time period t of
        # an indicator at clinic c
        for i in xrange(GraphicalClinicReport.n_indicators()):
            title = c_inds[0][i].title
            print title

            # Initialize data structure
            data = []
            for t in xrange(0, TwoMonthPeriodSet.num_periods):
                data.append([])

            for t in xrange(0, TwoMonthPeriodSet.num_periods):
                for c in xrange(0, len(clinics)):
                    val = c_inds[c][i].for_period_raw(TwoMonthPeriodSet, t)
                    print "%s: %s = %s" % (title, clinics[c], str(val) or '--')

                    data[t].append(val)
           
            flowable = [Paragraph(title, styleH3),
                        self._graph(data,\
                            map(unicode, clinics), TwoMonthPeriodSet)]

            last_row = table_data[len(table_data)-1]
            if len(last_row) < 2:
                last_row.append(flowable)
            else:
                table_data.append([flowable])

        story.append(Table(table_data, \
            style = [\
                ('ALIGN', (0,0), (-1, -1), 'CENTER'),\
                ('VALIGN', (0,0), (-1, -1), 'CENTER'),\
                ('LEFTPADDING', (0,0), (-1, -1), 30),\
                ('RIGHTPADDING', (0,0), (-1, -1), 30),\
                ('TOPPADDING', (0,0), (-1, -1), 30),\
                ('BOTTOMPADDING', (0,0), (-1, -1), 30),\
            ]))
        doc = SimpleDocTemplate(f, pagesize=landscape(A4), \
                                topMargin=(0.5 * inch), \
                                bottomMargin=(0.5 * inch))
                                
        doc.build(story)
        f.close()

    def _graph(self, data, labels, period_set):
        dh = 2.5 * inch
        dw = 4 * inch

        drawing = Drawing(dw, dh)

        bc = HorizontalBarChart()
        bc.setProperties({
            'x': 1 * inch,
            'y': 0 * inch,
            'height': dh - (0 * inch),
            'width': dw - (1 * inch),
            'data': data,
            'strokeWidth': 0,
            'barLabelFormat': \
                lambda val: ('          %d%%' % val) \
                    if val is not None else '--',
        })
        bc.valueAxis.setProperties({
            'forceZero': 1,
            'valueMin': 0,
            'valueMax': 100,
            'labelTextFormat': "%d%%",
        })
        bc.categoryAxis.setProperties({
            'categoryNames': labels,
        })

        from pprint import pprint
        pprint(bc.getProperties())
        drawing.add(bc)

        legend = Legend()
        legend.x = dw - (0.8 * inch)
        legend.y = dh - (0.4 * inch)
        legend.colorNamePairs = []
        for i in xrange(0, len(data)):
            legend.colorNamePairs.append(\
                (bc.bars[i].fillColor, period_set.period_name(i)))

        # For some reason these get drawn in the opposite
        # order as the bars by default
        legend.colorNamePairs.reverse()
        drawing.add(legend)

        return drawing
        
