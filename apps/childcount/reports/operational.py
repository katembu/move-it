#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

import time
import datetime

from django.template import Template, Context
from django.http import HttpResponseRedirect

from ccdoc import Document, Table, Paragraph, Text

from childcount.models.ccreports import TheCHWReport
from childcount.models.ccreports import OperationalReport
from childcount.reports.utils import render_doc_to_response


def operational_report(request, rformat="html"):
    if rformat == 'pdf':
        return HttpResponseRedirect('/static/childcount/reports/operationalreport.pdf')

    doc = Document(u'Operational Report')

    cols = OperationalReport().get_columns()

    t = Table(len(cols))

    # Get column abbreviations
    t.add_header_row(map(lambda col: Text(col['abbr']), cols))

    # Generate templates for each column
    templates = map(lambda col: Template(col['bit']), cols)

    for chw in TheCHWReport.objects.all():
        ctx = Context({'object': chw})

        # Render the templates for this CHW
        rowdata = map(lambda t: Text(t.render(ctx)), templates)
        t.add_row(rowdata)

    doc.add_element(t)

    key = Table(2, Text(u'Column Names'))
    key.add_header_row([Text(u'Column'), Text(u'Description')])
    for col in cols:
        key.add_row([Text(col['abbr']), Text(col['name'])])
    doc.add_element(key)

    return render_doc_to_response(request, rformat, 
        doc, 'operational-report')


