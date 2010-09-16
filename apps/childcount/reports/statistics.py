#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

import time
import datetime

from django.utils.translation import gettext_lazy as _
from django.db import connection

from ccdoc import Document, Table, Paragraph, Text

from reporters.models import Reporter
from childcount.reports.utils import render_doc_to_response

def incoming_msg_stats(request, rformat="html"):
    report_title = (u'Messages Sent Per Day')
    report_subtitle = (u'Includes all messages -- including rejected and invalid forms.')

    doc = Document(report_title, report_subtitle)

    t = Table(3)
    t.add_header_row([
        Text(_(u'Date')),

        Text(_(u'User')),
        Text(_(u'Number Entered'))])

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
    
    fname = u'forms-per-day-' + time.strftime('%Y-%m-%d')
    return render_doc_to_response(request, rformat, doc, fname)


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

