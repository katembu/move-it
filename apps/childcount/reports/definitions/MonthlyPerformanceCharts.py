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

from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import HorizontalBarChart

from childcount.models.ccreports import GraphicalClinicReport

from childcount.reports.utils import TwoMonthPeriodSet
from childcount.reports.report_framework import PrintedReport

styles = getSampleStyleSheet()
styleN = styles['Normal']
styleH = styles['Heading1']
styleH3 = styles['Heading3']

class Report(PrintedReport):
    title = 'Monthly Performance Charts'
    filename = 'monthly_performance_charts'
    formats = ('pdf',)

    def generate(self, rformat, title, filepath, data):
        
        if rformat != 'pdf':
            raise NotImplementedError('Can only generate PDF for performance charts')

        f = open(filepath, 'w')
        story = [Paragraph(unicode(title), styleH3)]

        '''
        clinics = GraphicalClinicReport.objects.order_by('name')
        for ind in GraphicalClinicReport.indicators:
            # Initialize data structure
            data = []
            for i in xrange(0, TwoMonthPeriodSet.num_periods):
                data.append([])

            for i in xrange(0, TwoMonthPeriodSet.num_periods):
                for c in clinics:
                    data[i].append(ind.for_period_raw(TwoMonthPeriodSet, i))
            
            story.append(self._graph(ind.title, data, labels))
        '''
        doc = SimpleDocTemplate(f, pagesize=landscape(A4), \
                                topMargin=(0 * inch), \
                                bottomMargin=(0 * inch))
        doc.build(story)
        f.close()

    def _graph(self, title, data, labels):
        dh = 4 * inch
        dw = 5 * inch
        margin = 0.25 * inch

        drawing = Drawing(dw, dh)

        bc = HorizontalBarChart()
        bc.x = bc.y = margin
        bc.height = dh - (2 * margin)
        bc.width = dw - (2 * margin)
        bc.data = data
        bc.strokeColor = colors.black
        bc.categoryAxis.categoryNames = labels
        drawing.add(bc)

        return drawing
        
