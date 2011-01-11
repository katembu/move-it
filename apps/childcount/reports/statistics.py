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
from childcount.reports.utils import render_doc_to_file
from childcount.reports.utils import report_filepath

"""
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

def encounters_annotated():
    h = HouseholdVisitReport.objects.all()
    h = h.values('encounter__encounter_date').annotate(Count('encounter__encounter_date'))
    return h.order_by('encounter__encounter_date')
"""


def form_reporting(\
        rformat,
        report_title,
        report_data,
        filepath):
    print rformat
    print 'Creating doc'
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

    print filepath
    return render_doc_to_file(filepath, rformat, doc)

def matching_message_stats(like_strings, unlike_strings = []):
    '''
    Custom SQL to do a GROUP BY date

    Returns an iterable of (date, identity, count)
    tuples describing the number of msgs sent
    the user with username "identity" on the
    given date that contain msg_string

    '''

    conn = connection.cursor()
    prefix = \
    '''
        SELECT 
            DATE(`date`) as `date`, 
            `identity`, 
            COUNT(*) as `count` 
        FROM `logger_ng_loggedmessage` 
    '''
    postfix = \
    '''
        AND `direction`="O" 
        GROUP BY 
            DATE(`date`), 
            `identity` 
        ORDER BY `date` ASC;
    '''
   
    if type(like_strings) == list:
        q = prefix
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
        q += postfix
        stats = conn.execute(q, like_strings + unlike_strings)
    else:
        stats = conn.execute(prefix + \
            ' WHERE ' + \
            like_strings + \
            ' ' + \
            postfix)

    return conn.fetchall()

