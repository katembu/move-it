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
    from reportlab.graphics.shapes import Drawing, String, Group
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
from childcount.models import PregnancyReport
from childcount.models.ccreports import TheCHWReport
from childcount.utils import RotatedParagraph

from libreport.pdfreport import PDFReport, p, pheader
from libreport.pdfreport import MultiColDocTemplate
from libreport.pdfreport import ScaledTable

styles = getSampleStyleSheet()
styleN = styles['Normal']
styleH = styles['Heading1']
styleH3 = styles['Heading3']

@login_required
def chw_performance(request):

    rpt = PDFReport()
    rpt.landscape = False
    rpt.setTitle(_('CHW Performance Report'))
    rpt.setFilename('chw_performance')
    rpt.setRowsPerPage(42)

    chws = TheCHWReport.objects.filter(is_active=True).all()[10:20]

    for chw in chws:
        rpt.setElements(pheader(chw.full_name(), style=styleH))

        '''
        rpt.setElements(p(">> %d" % chw.household_visit(date.today()-timedelta(60), date.today()-timedelta(30))))
        for (day,count) in chw.household_visits_for_month(30):
            rpt.setElements(p("%s - %d" % (day, count)))
        '''

        rpt.setElements(pheader(_(u'HH Visits Per Day (last month)'),style=styleH3))
        drawing = _hhvisit_graph(chw)
        rpt.setElements(drawing)

        rpt.setElements(pheader(_(u'Active Pregnancies (less than 10 months)'),style=styleH3))
        preg_tab = _pregnancy_table(chw)
        rpt.setElements(preg_tab)

        rpt.setPageBreak()
    return rpt.render()

def _pregnancy_table(chw):
    if chw.num_of_pregnant_women() <= 0:
        return p(_("No active pregnancies reported for " \
                "%(chwname)s") % {'chwname': chw.full_name()})

    tab_data = []
    tab_data.append([\
        _(u'Name'),\
        _(u'Latest Report'),\
        _(u"Current\nMonth of Preg."),\
        _(u'# ANC Visits'),\
        _(u'Weeks since ANC')])

    def latest_preg_rep(woman):
        return PregnancyReport\
            .objects\
            .filter(encounter__patient = woman)\
            .order_by('-encounter__encounter_date')[0]

    women = chw.pregnant_women()

    # Order women by their lastest pregnancy report date
    women.sort(lambda x,y: \
        cmp(latest_preg_rep(x).encounter.encounter_date, \
            latest_preg_rep(y).encounter.encounter_date))

    for woman in women:
        row = []
        row.append(p(woman.full_name()))

        prep = latest_preg_rep(woman)
        days_ago = float((date.today() - prep.encounter.encounter_date.date()).days)
        preg_mon = int(prep.pregnancy_month + (days_ago / 30.4))

        # Don't mention women who have given birth
        if preg_mon > 10: continue

        if prep.weeks_since_anc is not None:
            weeks_since_anc = int(prep.weeks_since_anc + (days_ago / 7))
        else:
            weeks_since_anc = 'No ANC'

        row.append(p(prep.encounter.encounter_date.strftime('%d-%b-%Y')))
        row.append(p(unicode(preg_mon)))
        row.append(p(unicode(prep.anc_visits)))
        row.append(p(unicode(weeks_since_anc)))

        tab_data.append(row)

    return [Table(tab_data)]


def _hhvisit_graph(chw):
    height = 3 * inch
    width  = 6 * inch
    margin = 0.5 * inch

    drawing = Drawing(margin, 3 * inch)

    lp = HorizontalLineChart()

    lp.x = margin
    lp.y = margin
    lp.height = height - (2 * margin)
    lp.width = width - (2 * margin)
    lp.joinedLines = 1

    [dates, counts] = zip(*chw.household_visits_for_month(30))
    if sum(counts) == 0:
        return p(_(u"No HH visits reported by %(chwname)s last month") % \
            {'chwname': chw.full_name()})

    lp.data = [counts]

    # Show date labels for every 4th day
    lp.categoryAxis.categoryNames = map(lambda n: \
        (date.today() + timedelta(n)).strftime('%d %b') \
        if n % 4 == 0
        else '', dates)

    drawing.add(lp)
    return [drawing]


