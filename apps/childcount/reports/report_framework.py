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
    result.wait()

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

class PrintedReport(Task):
    abstract = True
    
    title = None
    filename = None
    formats = []
    argvs = [] # Not used yet

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
        
        if len(self.argvs) == 0:
            self.generate(rformat)
        else:
            for args in self.argvs:
                self.generate(rformat, **kwargs)

        return True
        
    def generate(self, rformat, **kwargs):
        raise NotImplementedError(\
            _(u'Generate function not implemented.'))

    def get_filepath(self, rformat):
        if self.filename is None:
            raise ValueError(\
                _(u'Report filename is unset.'))
        return report_filepath(self.filename, rformat)

