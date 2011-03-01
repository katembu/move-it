#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import copy
import numpy

from django.utils.translation import gettext_lazy as _
from django.template import Template, Context
from locations.models import Location

try:
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.platypus import Paragraph, SimpleDocTemplate, PageBreak
    from reportlab.platypus import Table, TableStyle, NextPageTemplate
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
except ImportError:
    pass

from childcount.models import Clinic
from childcount.models import CHW
from childcount.models.ccreports import MonthlyCHWReport
from childcount.utils import RotatedParagraph
from childcount.reports.utils import render_doc_to_file, MonthlyPeriodSet
from childcount.reports.indicator import INDICATOR_EMPTY

from libreport.pdfreport import p

from childcount.reports.report_framework import PrintedReport

styles = getSampleStyleSheet()
styleN = styles['Normal']
styleH = styles['Heading1']
styleH3 = styles['Heading3']

class Report(PrintedReport):
    title = 'Operational Report - Monthly'
    filename = 'operational_report_monthly'
    formats = ('pdf',)

    def generate(self, rformat, title, filepath, data):
        '''
        Generate OperationalReport and write it to file
        '''
        
        if rformat != 'pdf':
            raise NotImplementedError('Can only generate PDF for operational report')


        f = open(filepath, 'w')

        story = []
        locations = Clinic.objects.filter(\
            pk__in=CHW.objects.values('clinic').distinct())[0:1]

        for location in locations:
            rowCHWs = MonthlyCHWReport\
                        .objects\
                        .filter(is_active=True)\
                        .filter(clinic=location)[0:1]
            if rowCHWs.count() == 0:
                continue

            tb = self._operationalreportable(location, rowCHWs)

            story.append(tb)
            story.append(PageBreak())

        doc = SimpleDocTemplate(f, pagesize=landscape(A4), \
                                topMargin=(0 * inch), \
                                bottomMargin=(0 * inch))
        doc.build(story)

        f.close()

    def _operationalreportable(self,title, indata=None):
        rowHeights = []
        styleH3.fontName = 'Times-Bold'
        styleH3.alignment = TA_CENTER
        styleH3.fontSize = 10
        styleN2 = copy.copy(styleN)
        styleN2.alignment = TA_CENTER
        styleN3 = copy.copy(styleN)
        styleN3.alignment = TA_RIGHT

        chw = indata[0]
        cols = filter(lambda i: i != INDICATOR_EMPTY, chw.report_indicators())

        ''' Header data '''
        hdata = [Paragraph('%s' % title, styleH3)]
        hdata.extend((len(cols) - 1) * [''])
        rowHeights.append(None)
        data = [hdata]
        ''' 
        data.append(['', Paragraph('Household', styleH3), '', '', \
                Paragraph('Newborn', styleH3), '', '', \
                Paragraph('Under-5\'s', styleH3), '', \
                '', '', '', '', Paragraph('Pregnant', styleH3), '', '', \
                Paragraph('Appointment', styleH3), '', \
                Paragraph('Follow-up', styleH3), '', \
                Paragraph('SMS', styleH3), '', \
                Paragraph('',
                            styleH3)])
        '''
        thirdrow = [Paragraph('CHW Name', styleH3)]
        # Column headers
        for ind in cols:
            p = RotatedParagraph(Paragraph((ind.title), styleN),\
                2.3*inch, 0.25*inch)
            thirdrow.append(p)

        data.append(thirdrow)
        rowHeights.append(2.3*inch)

        colWidths = [1.4 * inch]
        for c in cols:
            if c.is_percentage:
                colWidths.append(1.0 * inch)
            else:
                colWidths.append(0.4 * inch)
        ''' value_data contains the strings for each cell of the table.
            We need to format these into reportlab Paragraph objects
            with bold and underlining.

            agg_data has the summary figures for the bottom of the table.

            thresholds has a tuple (low, high) for the values below/above
            which a cell should be underlined/bolded.
        '''

        (value_data, agg_data, thresholds) = self._generate_stats(cols, indata)
        if len(value_data) > 0:
            rows = []
            for j, values in enumerate(value_data):
                row = [Paragraph(indata[j].full_name(), styleN)]

                for (i,colv) in enumerate(values):
                    row.append(Paragraph(unicode(colv), styleN))
                rows.append(row)
            
            rowHeights.extend((1+len(rows)) * [0.25 * inch])

            # Add data to table
            data.extend(rows)
            data.append(agg_data[0])

        tb = Table(data, colWidths=colWidths, rowHeights=rowHeights, repeatRows=6)
        tb.setStyle(TableStyle([('SPAN', (0, 0), (22, 0)),
                                ('INNERGRID', (0, 0), (-1, -1), 0.1, \
                                colors.lightgrey),\
                                ('BOX', (0, 0), (-1, -1), 0.1, \
                                colors.lightgrey), \
                                ('BOX', (1, 1), (3, -1), 2, \
                                colors.lightgrey),\
                                ('BOX', (7, 1), (12, -1), 2, \
                                colors.lightgrey),\
                                ('BOX', (16, 1), (17, -1), 2, \
                                colors.lightgrey),\
                                ('BOX', (20, 1), (21, -1), 2, \
                                colors.lightgrey),
                                ('LINEABOVE', (0, -3), (-1, -3), 1, \
                                colors.black)
                    ]))
        return tb

    def _generate_stats(self, cols, indata):
        value_data = []
        
        cols = filter(lambda i: i != INDICATOR_EMPTY, cols)
        aggregate_data = map(lambda x: [], cols)

        if not indata:
            return ([], [], [])

        for chw in indata:
            indicators = filter(lambda i: i != INDICATOR_EMPTY,
                chw.report_indicators())

            # Render column values into strings
            row_values = []
            for ind in indicators:
                ind.set_excel(False)
                row_values.append(ind.for_total(MonthlyPeriodSet))

            value_data.append(row_values)

            # Convert data to float for aggregation
            for (i,val) in enumerate(indicators):
                if val is None: continue
                if val == INDICATOR_EMPTY: continue

                elif val.is_percentage:
                    (n,d) = val.for_total_raw(MonthlyPeriodSet)
                    calc = float(n)/float(d)
                else:
                    calc = val.for_total_raw(MonthlyPeriodSet)

                aggregate_data[i].append(calc)

        thresholds = []
        aggregates = [[u'Average'], [u'Standard Deviation'], [u'Median']]
        for points in aggregate_data:
            if points:
                print points
                avg = numpy.average(points)
                std = numpy.std(points)
                med = numpy.median(points)
       

                aggregates[0].append(Paragraph(u"%0.1f" % avg, styleN))
                aggregates[1].append(Paragraph(u"%0.1f" % std, styleN))
                aggregates[2].append(Paragraph(u"%0.1f" % med, styleN))

                if int(std) == 0:
                    thresholds.append((float('-inf'), float('inf')))
                else:
                    thresholds.append((avg - (2*std), avg + (2*std)))
            else:
                for i in xrange(0,3):
                    aggregates[i].append(u'-') 
                thresholds.append(None)

        return (value_data, aggregates, thresholds)


