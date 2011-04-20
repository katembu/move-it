#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: mvpdev

import datetime

from django.utils.translation import gettext as _

from childcount.models import Patient
from childcount.models.ccreports import TheCHWReport, ClinicReport, ThePatient

from childcount.models.ccreports import SummaryReport, WeekSummaryReport
from childcount.models.ccreports import MonthSummaryReport
from childcount.models.ccreports import GeneralSummaryReport

from childcount.reports import report_framework
from childcount.reports.utils import report_modified_on

from django.utils import simplejson

def registration_chart():
    """
    this method corresponds to the template: 'dashboard_sections/registration_chart.html'
    it returns only the data needed to build the chart, which is passed to a javascript
    object in a JSON string using simplejson.dumps().
    """
    
    days_past, num_registrations = Patient.registrations_by_date()
    
    reg_chart_data = { 'yAxis': _(u"Total Number of Patients"), \
                       'xAxis': _(u"Number of days ago"),
            'daysPast' : days_past, 'regCount': num_registrations }
    
    return simplejson.dumps(reg_chart_data)


def highlight_stats_bar():
    """
    corresponds to template: 'dashboard_sections/highlight_stats_bar.html'
    
    This Dict is structured to easily pump into an html table.
    """
    return {'titles': [_(u"# of Households"), _(u"# of Patients"), \
                       _(u"# of Underfives"), _(u"# of Pregnant Women")], \
                        'data': [532, 1521, 534, 0] }

def nutrition_chart():
    """
    TheCHWReport.muac_summary()
    
    these 2 lines were working before:    
    nut_data = TheCHWReport.muac_summary_data()
    nutrition_data_for_dashboard = [["Unknown", nut_data['unknown']], \
                                    ["Healthy", nut_data['healthy']], \
                                    ["Moderate", nut_data['moderate']]]
    
    I'm pushing to a new branch with dummy data as an example.
    """
    nutrition_data_for_dashboard = [[_(u"Unknown"), 80], \
                                    [_(u"Healthy"), 17], \
                                    [_(u"Moderate"), 3]]
    
    return simplejson.dumps(nutrition_data_for_dashboard)

def recent_numbers():
    """
    pumps a python dict with "columns" and "rows"(&data) which is
    then turned into a pretty html table
    
    the WeekSummaryReport.summary() was not working so I left it out
    """

    generated_report_data = {'month': MonthSummaryReport.summary()['month_report'], \
                            'general': GeneralSummaryReport.summary()['general_summary_report'] }
    
    recent_numbers_columns = [[_(u"This Month"), 'month'], [_(u"Overall"), 'general']]
    named_rows = [[_(u"+SAM / MAM"),"num_mam_sam"], [_(u"Malaria"), 'num_rdt'], [_(u"Pregnancy"), 'num_pregnant']]
    
    recent_numbers_data = []
    for row in named_rows:
        row_id = row[1]
        recent_numbers_data.append([row[0], [generated_report_data[dt[1]][row_id] for dt in recent_numbers_columns]])
    
    return {'columns': [c[0] for c in recent_numbers_columns], 'rows': recent_numbers_data}
    
    

def reports_list():
    """
    
    report_sets was not exactly what I needed to I made a tiny change to how
    it is passed to the template.
    
    specifically, instead of
        report.types = ['html','xls']
    I used
        report.types = {'html':True, 'xls': False, 'pdf': True, 'csv': False}
    
    """
    report_sets_original = report_framework.report_sets()
    report_sets = []
    
    for reports in report_sets_original:
        rset_title = reports['name']
        rset_reports = []
        for rrr in reports['data']:
            
            temp_r = {
                'title': rrr['title'],
                'url': rrr['url'],
                'html': (False, None),
                'xls': (False, None),
                'pdf': (False, None),
                'csv': (False, None),
            }
            for rtype in rrr['types']:
                temp_r[rtype] = (True, \
                        report_modified_on(rrr['filename'], rtype))
            
            rset_reports.append(temp_r)
        
        report_sets.append({
            'title': rset_title,
            'show_datestamp': reports['show_datestamp'],
            'reports': rset_reports
        })
    return report_sets
