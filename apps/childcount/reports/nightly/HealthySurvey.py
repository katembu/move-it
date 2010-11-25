#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import copy

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
from childcount.models.ccreports import TheBHSurveyReport
from childcount.utils import RotatedParagraph

from libreport.pdfreport import p
from libreport.pdfreport import MultiColDocTemplate

from childcount.reports.utils import report_filepath
from childcount.reports.report_framework import PrintedReport

styles = getSampleStyleSheet()

styleN = styles['Normal']
styleH = styles['Heading1']
styleH3 = styles['Heading3']

class Report(PrintedReport):
    title = 'Healthy Survey Report'
    filename = 'healthy_survey'
    formats = ['pdf']

    def generate(self, rformat, **kwargs):
        '''
        Generate the healthy survey report.
        '''
        if rformat != 'pdf':
            raise NotImplementedError('Can only generate PDF for survey report')

        f = open(self.get_filepath(rformat), 'w')

        story = []

        clinics = Clinic.objects.all()
        for clinic in clinics:
            if not TheBHSurveyReport.objects.filter(clinic=clinic).count():
                continue
            tb = self.surveyreportable(clinic, TheBHSurveyReport.objects.\
                filter(clinic=clinic))
            story.append(tb)
            story.append(PageBreak())

        doc = SimpleDocTemplate(f, pagesize=landscape(A4), \
                                topMargin=(0 * inch), \
                                bottomMargin=(0 * inch))
        doc.build(story)
        f.close()


    def surveyreportable(self, title, indata=None):
        styleH3.fontName = 'Times-Bold'
        styleH3.alignment = TA_CENTER
        styleN2 = copy.copy(styleN)
        styleN2.alignment = TA_CENTER
        styleN3 = copy.copy(styleN)
        styleN3.alignment = TA_RIGHT

        cols = TheBHSurveyReport.healthy_survey_columns()

        hdata = [Paragraph('%s' % title, styleH3)]
        hdata.extend((len(cols) - 1) * [''])
        data = [hdata]

        thirdrow = [Paragraph(cols[0]['name'], styleH3)]
        thirdrow.extend([RotatedParagraph(Paragraph(col['name'], styleN), \
                                    2.3 * inch, 0.25 * inch) for col in cols[1:]])
        data.append(thirdrow)

        rowHeights = [None, 2.3 * inch]
        colWidths = [3.0 * inch]
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
        tb.setStyle(TableStyle([('SPAN', (0, 0), (colWidths.__len__() - 1, 0)),
                                ('INNERGRID', (0, 0), (-1, -1), 0.1, \
                                colors.lightgrey),\
                                ('BOX', (0, 0), (-1, -1), 0.1, \
                                colors.lightgrey),
                                ('BOX', (3, 1), (8, -1), 5, \
                                colors.lightgrey),
                                ('BOX', (8, 1), (9, -1), 5, \
                                colors.lightgrey),
                                ('BOX', (9, 1), (10, -1), 5, \
                                colors.lightgrey)]))
        return tb

