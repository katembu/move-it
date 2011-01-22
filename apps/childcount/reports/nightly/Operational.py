#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import copy
import numpy

from django.utils.translation import gettext_lazy as _
from django.template import Template, Context

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
from childcount.models.ccreports import TheCHWReport
from childcount.models.ccreports import OperationalReport
from childcount.utils import RotatedParagraph

from libreport.pdfreport import p

from childcount.reports.report_framework import PrintedReport

styles = getSampleStyleSheet()
styleN = styles['Normal']
styleH = styles['Heading1']
styleH3 = styles['Heading3']

class Report(PrintedReport):
    title = 'Operational Report'
    filename = 'operational_report'
    formats = ['pdf']

    def generate(self, rformat, title, filepath, data):
        '''
        Generate OperationalReport and write it to file
        '''
        
        if rformat != 'pdf':
            raise NotImplementedError('Can only generate PDF for operational report')

        f = open(filepath, 'w')

        story = []
        clinics = Clinic.objects.filter(pk__in=CHW.objects.values('clinic')\
                                                        .distinct('clinic'))
        for clinic in clinics:
            if not TheCHWReport.objects.filter(clinic=clinic).count():
                continue
            tb = self._operationalreportable(clinic, TheCHWReport.objects.\
                filter(clinic=clinic))
            story.append(tb)
            story.append(PageBreak())
            print clinic

        doc = SimpleDocTemplate(f, pagesize=landscape(A4), \
                                topMargin=(0 * inch), \
                                bottomMargin=(0 * inch))
        doc.build(story)

        f.close()

    def _operationalreportable(self,title, indata=None):
        styleH3.fontName = 'Times-Bold'
        styleH3.alignment = TA_CENTER
        styleH3.fontSize = 10
        styleN2 = copy.copy(styleN)
        styleN2.alignment = TA_CENTER
        styleN3 = copy.copy(styleN)
        styleN3.alignment = TA_RIGHT

        opr = OperationalReport()
        cols = opr.get_columns()

        hdata = [Paragraph('%s' % title, styleH3)]
        hdata.extend((len(cols) - 1) * [''])
        data = [hdata, ['', Paragraph('Household', styleH3), '', '', \
                Paragraph('Newborn', styleH3), '', '', \
                Paragraph('Under-5\'s', styleH3), '', \
                '', '', '', '', Paragraph('Pregnant', styleH3), '', '', \
                Paragraph('Appointment', styleH3), '', \
                Paragraph('Follow-up', styleH3), '', \
                Paragraph('SMS', styleH3), '', \
                Paragraph('',
                            styleH3)], \
                ['', Paragraph('A1', styleH3), Paragraph('A2', styleH3), \
                Paragraph('A3', styleH3), Paragraph('B1', styleH3), \
                Paragraph('B2', styleH3), Paragraph('B3', styleH3), \
                Paragraph('C1', styleH3), Paragraph('C2', styleH3), \
                Paragraph('C3', styleH3), Paragraph('C4', styleH3), \
                Paragraph('C5', styleH3), Paragraph('C6', styleH3), \
                Paragraph('D1', styleH3), Paragraph('D2', styleH3), \
                Paragraph('D3', styleH3), Paragraph('E1', styleH3),
                Paragraph('E2', styleH3), Paragraph('F1', styleH3), \
                Paragraph('F2', styleH3), Paragraph('G1', styleH3), \
                Paragraph('G2', styleH3), Paragraph('H1', styleH3)]]

        thirdrow = [Paragraph(cols[0]['name'], styleH3)]
        thirdrow.extend([RotatedParagraph(Paragraph(col['name'], styleN), \
                                    2.3 * inch, 0.25 * inch) for col in cols[1:]])
        data.append(thirdrow)

        fourthrow = [Paragraph('Target:', styleH3)]
        fourthrow.extend([Paragraph(item, styleN) for item in ['-', '-', '100', \
                            '-', '100', '100', '-', '-', '-', '-', '100', '-', \
                            '-', '-', '100', '', '100', '100', '&lt;=2', '0', \
                            '-', '100']])
        data.append(fourthrow)

        fifthrow = [Paragraph('<u>List of CHWs</u>', styleH3)]
        fifthrow.extend([Paragraph(item, styleN) for item in [''] * 19])
        data.append(fifthrow)

        rowHeights = [None, None, None, 2.3 * inch, 0.25 * inch, 0.25 * inch]
        colWidths = [1.7 * inch]
        colWidths.extend((len(cols) - 1) * [0.4 * inch])


        (value_data, thresholds) = self._generate_stats(cols, indata)
        if len(value_data) > 0:
            for values in value_data:
                row = []
                for (i,col) in enumerate(values):
                    if i == 0:
                        row.append(Paragraph(col, styleN))
                        continue

                    tag_open = tag_close = u''
                    colv = self._strip_junk(col)
                    if thresholds[i-1][0] and colv < thresholds[i-1][0]:
                        tag_open = u'<u>'
                        tag_close = u'</u>'
                    elif thresholds[i-1][0] and colv > thresholds[i-1][1]:
                        tag_open = u'<b>'
                        tag_close = u'</b>'

                    row.append(Paragraph(u"%s%s%s" % \
                        (tag_open, col, tag_close), styleN3)) 


            data.extend(value_data)
            rowHeights.extend(len(indata) * [0.25 * inch])
            rowHeights.extend(3 * [0.25 * inch])

        tb = Table(data, colWidths=colWidths, rowHeights=rowHeights, repeatRows=6)
        tb.setStyle(TableStyle([('SPAN', (0, 0), (22, 0)),
                                ('INNERGRID', (0, 0), (-1, -1), 0.1, \
                                colors.lightgrey),\
                                ('BOX', (0, 0), (-1, -1), 0.1, \
                                colors.lightgrey), \
                                ('BOX', (1, 1), (3, -1), 2, \
                                colors.lightgrey),\
                                ('SPAN', (1, 1), (3, 1)), \
                                ('SPAN', (4, 1), (6, 1)), \
                                ('BOX', (7, 1), (12, -1), 2, \
                                colors.lightgrey),\
                                ('SPAN', (7, 1), (12, 1)), \
                                ('SPAN', (13, 1), (15, 1)), \
                                ('BOX', (16, 1), (17, -1), 2, \
                                colors.lightgrey),\
                                ('SPAN', (16, 1), (17, 1)), \
                                ('SPAN', (18, 1), (19, 1)), \
                                ('SPAN', (20, 1), (21, 1)), \
                                ('BOX', (20, 1), (21, -1), 2, \
                                colors.lightgrey),
                                ('LINEABOVE', (0, -3), (-1, -3), 1, \
                                colors.black)
                    ]))
        return tb

    def _generate_stats(self, cols, indata):
        value_data = []
        aggregate_data = map(lambda x: [], cols[1:])

        if not indata:
            return ([], [])

        for chw in indata:
            ctx = Context({"object": chw})

            # Render column values into strings
            row_values = map(lambda col: Template(col['bit']).render(ctx), cols)
            value_data.append(row_values)

            for (i,val) in enumerate(row_values[1:]):
                val = self._strip_junk(val)
                if val:
                    aggregate_data[i].append(val)


        thresholds = []
        aggregates = []
        for points in aggregate_data:
            if points:
                avg = numpy.average(points)
                std = numpy.std(points)
                med = numpy.median(points)
        
                aggregates.append(("%0.1f" % avg, "%0.1f" % std, "%0.1f" % med))
                thresholds.append((avg - (2*std), avg + (2*std)))
            else:
                aggregates.append(('-','-','-'))
                thresholds.append([False, False])

        value_data.append(['Avgerage'] + map(lambda l: l[0], aggregates))
        value_data.append(['Standard Deviation'] + map(lambda l: l[1], aggregates))
        value_data.append(['Median'] + map(lambda l: l[2], aggregates))

        return (value_data, thresholds)


    def _strip_junk(self, v):
        v = v.replace('%', '').replace('-', '').replace(' ', '')
        if v == '':
            return None
        return float(v)


