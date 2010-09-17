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

def form_a_entered(request, rformat="html"):
    return _form_reporting(
        request,
        rformat,
        report_title = (u'Form A Registrations Per Day'),
        report_data = _matching_message_stats(['You successfuly registered ']),
        report_filename = u'form-a-entered')

def form_b_entered(request, rformat="html"):
    return _form_reporting(
        request,
        rformat,
        report_title = (u'Form Bs Entered Per Day'),
        report_data = _matching_message_stats(['Household member '], [' failed: ']),
        report_filename = u'form-b-entered')

def _form_reporting(request,
        rformat,
        report_title,
        report_data,
        report_filename):

    doc = Document(report_title, '')

    t = Table(3)
    t.add_header_row([
        Text(_(u'Date')),
        Text(_(u'User')),
        Text(_(u'Count'))])

    for row in report_data: 
        rowdate = time.strptime(unicode(row[0]), "%Y-%m-%d")
        username = row[1]
        full_name = u"[%s]" % username
        try:
            rep = Reporter.objects.get(username=username)
        except Reporter.DoesNotExist:
            pass
        else:
            full_name = u"%s %s [%s]" % (rep.first_name, rep.last_name, username)

        t.add_row([
            Text(row[0], castfunc = lambda a: a),
            Text(full_name),
            Text(row[2], castfunc = int)])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, doc, report_filename)


def _matching_message_stats(like_strings, unlike_strings = []):
    '''
    Custom SQL to do a GROUP BY date

    Returns an iterable of (date, identity, count)
    tuples describing the number of msgs sent
    the user with username "identity" on the
    given date that contain msg_string

    '''

    conn = connection.cursor()
    q = \
    '''
        SELECT 
            DATE(`sent`) as `date`, 
            `identity`, 
            COUNT(*) as `count` 
        FROM `logger_outgoingmessage` 
    '''
    
    if len(like_strings) + len(unlike_strings) > 0:
        q += ' WHERE '

    andstr = ' AND '
    locstr = ' LOCATE(%s, `text`) '

    for i in xrange(len(like_strings)):
        q += locstr
        if i+1 != len(like_strings):
            q += andstr
           
    if len(unlike_strings) > 0:
        q += andstr

    for i in xrange(len(unlike_strings)):
        q += ' NOT ' + locstr
        if i+1 != len(unlike_strings):
            q += andstr

    q += \
    '''
        GROUP BY 
            DATE(`sent`), 
            `identity` 
        ORDER BY `sent` ASC;
    '''
   
    print q
    stats = conn.execute(q, like_strings + unlike_strings)
    return conn.fetchall()

