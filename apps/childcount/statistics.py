#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

import time
import datetime

from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
from django.db import connection

from rapidsms.webui.utils import render_to_response

from ccdoc import Document, Table, Paragraph, Text
from ccdoc import PDFGenerator, HTMLGenerator, ExcelGenerator

from reporters.models import Reporter

def incoming_msg_stats(request, rformat="html"):
    report_title = ('Messages Sent Per Day')
    report_subtitle = ('Includes all messages -- including rejected and invalid forms.')

    doc = Document(report_title, report_subtitle)

    t = Table(3)
    t.add_header_row([
        Text(_('Date')),
        Text(_('User')),
        Text(_('Number Entered'))])

    report_data = _incoming_msg_stats()

    for row in report_data:
        username = row[3]
        full_name = u"[%s]" % username
        try:
            rep = Reporter.objects.get(username=username)
        except Reporter.DoesNotExist:
            pass
        else:
            full_name = u"%s %s [%s]" % (rep.first_name, rep.last_name, username)

        t.add_row([
            Text(datetime.date(row[0], row[1], row[2]).strftime('%Y-%m-%d')),
            Text(full_name),
            Text(row[4])])
    doc.add_element(t)
    
    fname = _('forms-per-day-') + unicode(time.strftime('%Y-%m-%d'))
    return _render_doc_to_response(request, rformat, doc, fname)


def _render_doc_to_response(request, rformat, doc, filebasename = _('report')):
    tstart = time.time()
    h = None
    response = HttpResponse()

    # Don't cache the report
    response['Cache-Control'] = ''

    if rformat == 'html':
        h = HTMLGenerator(doc)
        response['Content-Type'] = 'text/html'
    elif rformat == 'xls':
        h = ExcelGenerator(doc)
        response['Content-Disposition'] = "attachment; " \
              "filename=\"%s.xls\"" % filebasename
        response['Content-Type'] = 'application/vnd.ms-excel'
    elif rformat == 'pdf':
        h = PDFGenerator(doc)
        response['Content-Disposition'] = "attachment; " \
              "filename=\"%s.pdf\"" % filebasename
        response['Content-Type'] = 'application/pdf'
    else:
        raise ValueError('Invalid report format')

    h.render_document()
    response.write(h.get_contents())
    print "=== FINISHED IN %lg SECONDS ===" % (time.time() - tstart)
    return response

def _incoming_msg_stats():
    '''
    Custom SQL to do a GROUP BY day

    Returns an iterable...each item has 
    methods year, month, day, identity, and count,
    describing the number of msgs received from
    the user with username "identity" on the
    given date.

    '''

    conn = connection.cursor()
    stats = conn.execute(
        '''
        SELECT 	
            YEAR(`received`) as `year`,
            MONTH(`received`) as `month`,
            DAY(`received`) as `day`,
            identity,
            COUNT(*) as `count`
        FROM `logger_incomingmessage`
        GROUP BY
            YEAR(`received`),
            MONTH(`received`),
            DAY(`received`),
            `identity`
        ORDER BY `received` ASC;
        ''')

    return conn.fetchall()

