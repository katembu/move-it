import time
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import os
import shutil

from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse

from rapidsms.webui.utils import render_to_response

from childcount.utils import first_date_of_week

from ccdoc import PDFGenerator, HTMLGenerator, ExcelGenerator

REPORTS_DIR = 'reports'

# Monthly (w1, w2, w3, w4)
# Quarterly (J, F, M, A, ...)
# Annual (q1, q2, q3, q4)

"""
PeriodSet is for representing a set of
time periods that you would use to generate
a report.

For example, MonthlyPeriodSet describes
the beginning and ends of each week in
the month.
"""

class PeriodSet(object):
    num_periods = None
    total_name = None

    @classmethod
    def enum_periods(cls):
        periods = []
        for i in xrange(0, cls.num_periods):
            periods.append(cls.period_name(i))
        return enumerate(periods)
    
    @classmethod
    def period_name(cls, period_num):
        raise NotImplementedError('No period name function')

    @classmethod
    def period_start_date(cls, period_num):
        raise NotImplementedError('No period start date function')

    """
    End date is the start date of the *next* period
    minus one day
    """
    @classmethod
    def period_end_date(cls, period_num):
        return cls.period_start_date(period_num+1) - \
            timedelta(1)

class MonthlyPeriodSet(PeriodSet):
    num_periods = 4
    total_name = 'M'

    @classmethod
    def period_name(cls, period_num):
        return "W%d" % (period_num + 1)

    @classmethod
    def period_start_date(cls, week_num):
        first_day_of_month = date.today() - \
                timedelta(35) - \
                relativedelta(day=1)
        return first_date_of_week(first_day_of_month) + \
            timedelta(week_num * 7)

class QuarterlyPeriodSet(PeriodSet):
    num_periods = 3
    total_name = 'Q'

    @classmethod
    def period_name(cls, period_num):
        return self\
            .period_start_date(period_num)\
            .strftime('%b')

    @classmethod
    def period_start_date(cls, month_num):
        first_day_of_quarter = date.today() - \
            timedelta(4 * 30.475) - \
            relativedelta(day=1)

        return first_day_of_quarter + \
            timedelta(month_num * 32) - \
            relativedelta(day=1)

class AnnualPeriodSet(PeriodSet):
    num_periods = 4
    total_name = 'Y'

    @classmethod
    def period_name(cls, period_num):
        return "Q%d" % (period_num + 1)

    @classmethod
    def period_start_date(cls, q_num):
        first_day_of_year = date.today() - \
            relativedelta(month=1, day=1)

        return first_day_of_year + \
            timedelta(30.473 * 3 * q_num) - \
            relativedelta(day=1)

def render_doc_to_file(filename, rformat, doc):
    h = None 

    if rformat == 'html':
        h = HTMLGenerator(doc, filename)
    elif rformat == 'xls':
        h = ExcelGenerator(doc, filename)
    elif rformat == 'pdf':
        h = PDFGenerator(doc, filename)
    else:
        raise ValueError('Invalid report format')

    print 'Rendering doc'
    h.render_document()
    print 'Done rendering'
    print filename
 
def render_doc_to_response(request, rformat, doc,
        filebasename = _(u'report')):
    tstart = time.time()
    h = None

    if rformat == 'html':
        h = HTMLGenerator(doc)
    elif rformat == 'xls':
        h = ExcelGenerator(doc)
    elif rformat == 'pdf':
        h = PDFGenerator(doc)
    else:
        raise ValueError('Invalid report format')

    h.render_document()
    print h.get_filename()

    shutil.move(h.get_filename(), report_filepath(filebasename, rformat))
    print "=== FINISHED IN %lg SECONDS ===" % (time.time() - tstart)
    return HttpResponseRedirect(report_url(filebasename, rformat))

def report_filepath(rname, rformat):
    return os.path.join(\
                    os.path.dirname(__file__), \
                    '..',
                    'static',
                    REPORTS_DIR,
                    rname+'.'+rformat)

def report_url(rname, rformat):
    return ''.join([\
        '/static/childcount/',
        REPORTS_DIR,'/',
        rname,'.',rformat
    ])
