#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga
from datetime import datetime

from django.utils.translation import gettext as _
from django.template import Template, Context

from ccdoc import Document, Table, Paragraph, \
    Text, Section, PageBreak
from childcount.reports.utils import render_doc_to_file
from childcount.reports.utils import YearlyPeriodSet
from childcount.reports.report_framework import PrintedReport
from childcount.models.ccreports import HealthCoordinatorReport
from  childcount.models import Encounter


class Report(PrintedReport):
    title = _(u"CC+ HC Report")
    filename = 'health_coordinator'
    formats = ['xls', 'html']
    variants = [ (u'%s' % dt.year, u'%s' % dt.year, {'year': dt.year}) for dt in Encounter.objects.dates('encounter_date', 'year')]

    def generate(self, rformat, title, filepath, data):
        doc = Document(title)
        header = [u'']
        year = data['year']
        yps = YearlyPeriodSet(year=year)
        header.extend([yps.period_name(p) \
                        for p in xrange(0, yps.num_periods)])
        t = Table(header.__len__())
        t.add_header_row(map(Text, header))
        hcr = HealthCoordinatorReport()
        for indicator in hcr.report_indicators():
            if rformat in ('html', 'pdf'):
                indicator.set_excel(False)
            cols = [indicator.title]
            cols.extend([indicator.for_period(yps, p) \
                for p in xrange(0, YearlyPeriodSet.num_periods)])
            t.add_row(map(Text, cols))
            print indicator.title
        doc.add_element(Paragraph(_(u"For year %(year)s") % {'year': yps.year}))
        doc.add_element(t)
        return render_doc_to_file(filepath, rformat, doc)

    def _str_months_of_the_year(self, year=datetime.today().year):
        '''Return a list of months as text'''
        months = []
        for dt in self._months_of_the_year(year):
            months.append(dt.strftime('%b'))
        return months

    def _months_of_the_year(self, year=datetime.today().year):
        '''Returns the date of 1st of every month of the year'''
        months = []
        for i in range(12):
            months.append(datetime(year, i + 1, 1).date())
        return months
