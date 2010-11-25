#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga
from datetime import datetime

from django.utils.translation import gettext_lazy as _
from django.template import Template, Context

from childcount.models import CHW
from childcount.models.reports import BedNetReport
from childcount.models.ccreports import TheBHSurveyReport

import ccdoc 
from childcount.reports.utils import render_doc_to_file
from childcount.reports.report_framework import PrintedReport

from locations.models import Location

class Report(PrintedReport):
    title = 'Household Healthy Survey Report'
    filename = 'healthy_survey'
    formats = ['pdf','xls','html']

    def generate(self, rformat, **kwargs):
        doc = ccdoc.Document(u'Household Healthy Survey Report')
        today = datetime.today()
        locations = Location.objects.filter(pk__in=CHW.objects.values('location')\
                                                        .distinct('location'))
        headings = TheBHSurveyReport.healthy_survey_columns()
        for location in locations:
            brpts = BedNetReport.objects.filter(encounter__chw__location=location)
            if not brpts.count():
                continue
            t = ccdoc.Table(headings.__len__())
            t.add_header_row([
                        ccdoc.Text(c['name']) for c in headings])
            for row in TheBHSurveyReport.objects.filter(location=location):
                ctx = Context({"object": row})
                row = []
                for cell in headings:
                    cellItem = Template(cell['bit']).render(ctx)
                    if cellItem.isdigit():
                        cellItem = int(cellItem)
                    cellItem = ccdoc.Text(cellItem)
                    row.append(cellItem)
                t.add_row(row)
            doc.add_element(ccdoc.Section(u"%s" % location))
            doc.add_element(t)
        return render_doc_to_file(\
            self.get_filepath(rformat), rformat, doc)

