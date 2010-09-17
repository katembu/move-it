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
    report_title = (u'Form A Registrations Per Day')
    doc = Document(report_title, '')

    t = Table(3)
    t.add_header_row([
        Text(_(u'Date')),
        Text(_(u'User')),
        Text(_(u'Number Entered'))])

    report_data = _incoming_msg_stats()

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
            Text(row[0]),
            Text(full_name),
            Text(row[2])])
    doc.add_element(t)
    
    fname = u'forms-per-day-' + time.strftime('%Y-%m-%d')
    return render_doc_to_response(request, rformat, doc, fname)


def _incoming_msg_stats():
    '''
    Custom SQL to do a GROUP BY day

    Returns an iterable of (date, identity, count)
    tuples describing the number of msgs received from
    the user with username "identity" on the
    given date.

    '''

    conn = connection.cursor()
    stats = conn.execute(
    '''
        SELECT 
            DATE(`sent`) as `date`, 
            `identity`, 
            COUNT(*) as `count` 
        FROM `logger_outgoingmessage` 
        WHERE 
            LOCATE("You successfuly registered ", `text`)
        GROUP BY 
            DATE(`sent`), 
            `identity` 
        ORDER BY `sent` ASC;
    ''')
    return conn.fetchall()

