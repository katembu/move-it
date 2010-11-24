#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

import shutil

from celery.task import Task
from celery.task.schedules import crontab

from django.utils.translation import gettext as _
from django.http import HttpResponseRedirect, HttpResponseNotFound

from childcount.models import Configuration as Cfg
from childcount.reports.utils import report_filepath, report_url

REPORTS_DIR = 'reports'

# CREATING A NEW REPORT:
# 1) Subclass PrintedReport to create a new nightly
#    or on-demand report
# 2) Put your report file in reports/nightly or
#    reports/ondemand as desired
# 3) Add the name of your report as a Configuration
#    in the DB

class PrintedReport(Task):
   
    # Human-readable title of report
    title = None
    # Filename alphanumeric, underscore, and hyphen are ok
    filename = None
    # A list of file formats to use, e.g., ['pdf','html','xls']
    formats = []

    variants = [
        #(title_suffix, fn_suffix, kwargs)

        # For example, you might have a patient register
        # for Bugongi and Ruhiira health centers: 
        #(' Bugongi HC', '_BG', {'clinic_id': 13}),
        #(' Ruhiira HC', '_RH', {'clinic_id': 15}).
    ]

    # You should implement the generate method in a report
    # subclass.  This method creates the report and saves it
    # to the right place (probably static/reports/filename.format).
    # The return value is ignored.
    def generate(self, rformat, **kwargs):
        raise NotImplementedError(\
            _(u'Generate function not implemented.'))

    ####################
    # Unless you're an expert, you don't need to override
    # any of the rest of the methods in your subclass


    abstract = True
    def __init__(self):
        pass

    def run(self, *args, **kwargs):
        if len(self.formats) == 0:
            raise ValueError(\
                _(u'This report has no formats specified.'))

        if 'rformat' not in kwargs:
            raise ValueError(\
                _(u'You must specify a report format.'))
        rformat = kwargs['rformat']

        if self.title is None or self.filename is None:
            raise ValueError(\
                _(u'Report title or filename is unset.'))
       
        if len(self.variants) == 0:
            self.generate(rformat)
            return True

        for i in enumerate(self.variants):
            print self.variants[i[0]]
            self.generate(rformat, var_index = i[0])
        
    def get_filepath(self, rformat):
        if self.filename is None:
            raise ValueError(\
                _(u'Report filename is unset.'))
        return report_filepath(self.filename, rformat)



#
# Misc.
#

def serve_ondemand_report(request, rname, rformat):
    repts = report_objects('ondemand')

    # Find reports matching requests
    matches = filter(lambda rep: \
        rep.filename == rname and rformat in rep.formats,
        repts)

    if len(matches) == 0:
        return HttpResponseNotFound(request)

    # If found, generate the report
    report = matches[0]
    result = report().apply(kwargs={'rformat':rformat})
    
    try:
        result.wait()
    except:
        print result.traceback
        raise

    if result.successful():
        # Redirect to static report
        return HttpResponseRedirect(report_url(rname, rformat))
    else:
        print result.traceback
        raise RuntimeError('Report generation failed')


def report_objects(folder):
    if folder not in ['nightly','ondemand']:
        raise ValueError('Folder specified must be "nightly" or "ondemand"')

    reports = []
    
    # Don't catch exception
    rvalues = Cfg.objects.get(key=folder+'_reports').value
    rnames = rvalues.split()
  
    print "Starting"
    for reporttype in rnames:
        print "Looking for module %s" % reporttype
        # Get childcount.reports.folder.report_name.Report
        try:
            rmod = __import__(\
                ''.join(['childcount.reports.',folder,'.',reporttype]),
                globals(), \
                locals(), \
                ['Report'], \
                -1)
        except ImportError:
            print "COULD NOT FIND MODULE %s" % reporttype
        else:
            print "Found module %s" % reporttype
            reports.append(rmod.Report)
    return reports
