#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

from celery.task import Task
from celery.task.schedules import crontab

from django.utils.translation import gettext as _

from childcount.models import Configuration as Cfg
from childcount.reports.utils import report_filename

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
    order = 0

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

    def get_filename(self, rformat):
        if self.filename is None:
            raise ValueError(\
                _(u'Report filename is unset.'))
        return report_filename(\
            ''.join([self.filename,'.',rformat]))

