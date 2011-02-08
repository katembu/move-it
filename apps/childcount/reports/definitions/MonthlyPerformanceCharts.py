#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from fractions import Fraction

from django.utils.translation import gettext as _

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import inch

from reportlab.platypus import Paragraph, SimpleDocTemplate
from reportlab.platypus import Table

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

class Percentage(Fraction):
    """
    I'm sorry for defining this class. The point is to
    be able to give the reportlab charting library an
    Integral-derived object on the scale of [0, 100]
    so that it can draw the chart,
    but we want to be able to display the numerator and
    denominator ints as labels on the bar graphs. 

    Python's fractions.Fraction is close, but if the
    numerator is zero, then the denominator info is lost.
    """

    num = 0
    den = 1
    empty = False

    def __str__(self):
        return unicode(self)

    def __unicode__(self):
        s = ' ' * 25
        if self.empty:
            return s + _(u"(No data)")
        else:
            return "%s%d%% (%d/%d)" % \
                (s, int(self), self.num / 100, self.den)

    def __new__(cls, n, d):

        empty = (d == 0)
        obj = super(Percentage,cls)\
            .__new__(cls, 100*n, 1 if empty else d)
        obj.num = n
        obj.den = d
        obj.empty = empty
        return obj


class Report(PrintedReport):
    title = _(u'Monthly Performance Charts')
    filename = 'monthly_performance_charts'
    formats = ('pdf',)

    def generate(self, rformat, title, filepath, data):
        
        if rformat != 'pdf':
            raise NotImplementedError(\
                _(u'Can only generate PDF for performance charts'))

        f = open(filepath, 'w')
        story = [Paragraph(unicode(title), styleH),\
            Paragraph(_(u"For months %(first)s and %(second)s") \
                % {'first': TwoMonthPeriodSet.period_name(1), \
                    'second': TwoMonthPeriodSet.period_name(0)}, \
                    styleN)]

        clinics = GraphicalClinicReport\
            .objects\
            .order_by('name')\
            .exclude(code='ZZZZ')

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
                    # We get a Fraction back, multiply by 100 to get a percentage
                    val = c_inds[c][i].for_period_raw(TwoMonthPeriodSet, t)
                    if val is not None:
                        val = Percentage(val[0], val[1])
                    else:
                        val = Percentage(0, 0)

                    print val
                    print "%s: %s = %s" % (title, clinics[c], val or '--')

                    data[t].append(val)
           
            flowable = [Paragraph(title, styleH3),
                        self._graph(data,\
                            map(lambda c: c.name, clinics), TwoMonthPeriodSet)]

            last_row = table_data[len(table_data)-1]
            if len(last_row) < 2:
                last_row.append(flowable)
            else:
                table_data.append([flowable])

        story.append(Table(table_data, \
            style = [\
                ('ALIGN', (0,0), (-1, -1), 'CENTER'),\
                ('VALIGN', (0,0), (-1, -1), 'CENTER'),\
                ('LEFTPADDING', (0,0), (-1, -1), 15),\
                ('RIGHTPADDING', (0,0), (-1, -1), 15),\
                ('TOPPADDING', (0,0), (-1, -1), 15),\
                ('BOTTOMPADDING', (0,0), (-1, -1), 15),\
            ]))
        doc = SimpleDocTemplate(f, pagesize=landscape(A4), \
                                topMargin=(0.1 * inch), \
                                bottomMargin=(0.1 * inch),\
                                leftMargin=(0.1 * inch),\
                                rightMargin=(0.1 * inch))
                                
        doc.build(story)
        f.close()

    def _graph(self, data, labels, period_set):
        dh = 2 * inch
        dw = 3.5 * inch

        drawing = Drawing(dw, dh)

        bc = HorizontalBarChart()
        bc.setProperties({
            'x': 1 * inch,
            'y': 0 * inch,
            'height': dh - (0 * inch),
            'width': dw - (1.5 * inch),
            'data': data,
            'strokeWidth': 0,
            'barLabelFormat': unicode,
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
        legend.x = dw
        legend.y = dh
        legend.colorNamePairs = []
        legend.boxAnchor = 'nw'
        for i in xrange(0, len(data)):
            legend.colorNamePairs.append(\
                (bc.bars[i].fillColor, period_set.period_name(i)))
        #pprint(legend.getProperties())

        # For some reason these get drawn in the opposite
        # order as the bars by default
        legend.colorNamePairs.reverse()
        drawing.add(legend)

        return drawing
        
