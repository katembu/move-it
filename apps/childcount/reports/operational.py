#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

import time
import datetime

from django.utils.translation import gettext_lazy as _
from django.db import connection
from django.db.models import Count

from ccdoc import Document, Table, Paragraph, Text

from reporters.models import Reporter
from childcount.models import HouseholdVisitReport
from childcount.reports.utils import render_doc_to_response

def encounters_per_day(request, rformat="html"):
    doc = Document(u'Encounters Per Day')
    h = encounters_annotated()

    t = Table(2)
    t.add_header_row([
        Text(u'Date'),
        Text(u'Count')])
    for row in h:
        t.add_row([
            Text(unicode(row['encounter__encounter_date'].date())), 
            Text(int(row['encounter__encounter_date__count']))])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, 
        doc, 'encounters-by-date')

def _form_reporting(request,
        rformat,
        report_title,
        report_data,
        report_filename):

    doc = Document(unicode(report_title), '')

    t = Table(3)
    t.add_header_row([
        Text(u'Date'),
        Text(u'User'),
        Text(u'Count')])

    for row in report_data: 
        username = row[1]
        full_name = u"[%s]" % username
        try:
            rep = Reporter.objects.get(username=username)
        except Reporter.DoesNotExist:
            pass
        else:
            full_name = u"%s %s [%s]" % (rep.first_name, rep.last_name, username)

        t.add_row([
            Text(unicode(row[0])),
            Text(full_name),
            Text(int(row[2]))])
    doc.add_element(t)

    return render_doc_to_response(request, rformat,
        doc, report_filename)


