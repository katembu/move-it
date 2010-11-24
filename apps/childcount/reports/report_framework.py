#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

from celery.task import Task
from celery.task.schedules import crontab

from django.utils.translation import gettext as _

from childcount.reports.utils import report_filename

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

