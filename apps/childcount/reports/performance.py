#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.template import Template, Context

from cStringIO import StringIO

try:
    from reportlab.graphics.charts.linecharts import HorizontalLineChart
    from reportlab.graphics.shapes import Drawing
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
from childcount.models.ccreports import TheCHWReport
from childcount.utils import RotatedParagraph

from libreport.pdfreport import PDFReport, p, pheader
from libreport.pdfreport import MultiColDocTemplate
from libreport.pdfreport import ScaledTable

@login_required
def chw_performance(request):
    styles = getSampleStyleSheet()

    styleN = styles['Normal']
    styleH = styles['Heading1']
    styleH3 = styles['Heading3']

    rpt = PDFReport()
    rpt.landscape = True
    rpt.setTitle(_('CHW Performance Report'))
    rpt.setFilename('chw_performance')
    rpt.setRowsPerPage(42)

    chws = TheCHWReport.objects.filter(is_active=True).all()[10:20]

    for chw in chws:
        rpt.setElements(pheader(chw.full_name(), style=styleH))

        rpt.setElements(p(">> %d" % chw.household_visit(date.today()-timedelta(60), date.today()-timedelta(30))))
        for (day,count) in chw.household_visits_for_month(30):
            rpt.setElements(p("%s - %d" % (day, count)))

        drawing = Drawing(600, 400)
        lp = HorizontalLineChart()
        lp.x = 50
        lp.y = 50
        lp.height = 325
        lp.width = 525
        lp.data = chw.household_visits_for_month(30)
        lp.joinedLines = 1
        drawing.add(lp)
        rpt.setElements([drawing])


        for woman in chw.pregnant_women():
            rpt.setElements(p(woman.full_name()))

        rpt.setPageBreak()

    return rpt.render()

