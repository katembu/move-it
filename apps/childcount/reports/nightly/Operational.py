#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import os
import copy
import csv
import cProfile
from time import time
from datetime import datetime
from types import StringType

from rapidsms.webui.utils import render_to_response

from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.template import Template, Context
from django.http import HttpResponse
from django.db.models import F

from cStringIO import StringIO

try:
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import letter, landscape, A4
    from reportlab.platypus import Paragraph, SimpleDocTemplate, PageBreak
    from reportlab.platypus import Table, TableStyle, NextPageTemplate
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
except ImportError:
    pass

from childcount.models import Clinic
from childcount.models import CHW
from childcount.models.reports import BedNetReport
from childcount.models.ccreports import TheCHWReport
from childcount.models.ccreports import ThePatient, OperationalReport
from childcount.models.ccreports import OperationalReport
from childcount.models.ccreports import ClinicReport
from childcount.models.ccreports import TheBHSurveyReport
from childcount.utils import RotatedParagraph

from libreport.pdfreport import PDFReport, p
from libreport.csvreport import CSVReport
from libreport.pdfreport import MultiColDocTemplate
from libreport.pdfreport import ScaledTable

import ccdoc 
from childcount.reports.utils import render_doc_to_response
from childcount.reports.utils import report_filepath
from childcount.reports.report_framework import PrintedReport

from locations.models import Location

styles = getSampleStyleSheet()
styleN = styles['Normal']
styleH = styles['Heading1']
styleH3 = styles['Heading3']

class Report(PrintedReport):
    title = 'Operational Report'
    filename = 'operational_report'
    formats = ['pdf']
    argvs = []
    order = 0

    def generate(self, rformat, **kwargs):
        '''
        Generate OperationalReport and write it to file
        '''
        
        if rformat != 'pdf':
            raise NotImplementedError('Can only generate PDF for operational report')

        filename = self.get_filepath(rformat) 
        f = open(filename, 'w')

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

        doc = SimpleDocTemplate(f, pagesize=landscape(A4), \
                                topMargin=(0 * inch), \
                                bottomMargin=(0 * inch))
        doc.build(story)

        f.close()

    def _operationalreportable(self,title, indata=None):
        styleH3.fontName = 'Times-Bold'
        styleH3.alignment = TA_CENTER
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
                Paragraph('Follow-up', styleH3), '', \
                Paragraph('SMS', styleH3), ''], \
                ['', Paragraph('A1', styleH3), Paragraph('A2', styleH3), \
                Paragraph('A3', styleH3), Paragraph('B1', styleH3), \
                Paragraph('B2', styleH3), Paragraph('B3', styleH3), \
                Paragraph('C1', styleH3), Paragraph('C2', styleH3), \
                Paragraph('C3', styleH3), Paragraph('C4',  styleH3), \
                Paragraph('C5', styleH3), Paragraph('C6', styleH3), \
                Paragraph('D1', styleH3), Paragraph('D2', styleH3), \
                Paragraph('D3', styleH3), Paragraph('E1', styleH3), \
                Paragraph('E2', styleH3), Paragraph('F1', styleH3), \
                Paragraph('F2', styleH3)]]

        thirdrow = [Paragraph(cols[0]['name'], styleH3)]
        thirdrow.extend([RotatedParagraph(Paragraph(col['name'], styleN), \
                                    2.3 * inch, 0.25 * inch) for col in cols[1:]])
        data.append(thirdrow)

        fourthrow = [Paragraph('Target:', styleH3)]
        fourthrow.extend([Paragraph(item, styleN) for item in ['-', '-', '100', \
                            '-', '100', '100', '-', '-', '-', '-', '100', '-', \
                            '-', '-', '100', '100', '&lt;=2', '0', '-']])
        data.append(fourthrow)

        fifthrow = [Paragraph('<u>List of CHWs</u>', styleH3)]
        fifthrow.extend([Paragraph(item, styleN) for item in [''] * 19])
        data.append(fifthrow)

        rowHeights = [None, None, None, 2.3 * inch, 0.25 * inch, 0.25 * inch]
        colWidths = [1.5 * inch]
        colWidths.extend((len(cols) - 1) * [0.5 * inch])

        if indata:
            for row in indata:
                ctx = Context({"object": row})
                values = [Paragraph(Template(cols[0]["bit"]).render(ctx), \
                                    styleN)]
                values.extend([Paragraph(Template(col["bit"]).render(ctx), \
                                    styleN3) for col in cols[1:]])
                data.append(values)
            rowHeights.extend(len(indata) * [0.25 * inch])
        tb = Table(data, colWidths=colWidths, rowHeights=rowHeights, repeatRows=6)
        tb.setStyle(TableStyle([('SPAN', (0, 0), (19, 0)),
                                ('INNERGRID', (0, 0), (-1, -1), 0.1, \
                                colors.lightgrey),\
                                ('BOX', (0, 0), (-1, -1), 0.1, \
                                colors.lightgrey), \
                                ('BOX', (1, 1), (3, -1), 5, \
                                colors.lightgrey),\
                                ('SPAN', (1, 1), (3, 1)), \
                                ('SPAN', (4, 1), (6, 1)), \
                                ('BOX', (7, 1), (12, -1), 5, \
                                colors.lightgrey),\
                                ('SPAN', (7, 1), (12, 1)), \
                                ('SPAN', (13, 1), (15, 1)), \
                                ('BOX', (16, 1), (17, -1), 5, \
                                colors.lightgrey),\
                                ('SPAN', (16, 1), (17, 1)), \
                                ('SPAN', (-2, 1), (-1, 1)), \
                    ]))
        return tb

