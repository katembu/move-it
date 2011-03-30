#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

import shutil
from datetime import datetime

from celery.task import Task
from celery.task.schedules import crontab

from django.utils.translation import gettext as _
from django.http import HttpResponseRedirect, HttpResponseNotFound

from reportgen.utils import report_filepath, report_url
from reportgen.models import GeneratedReport

NIGHTLY_DIR = 'nightly'
ONDEMAND_DIR = 'ondemand'

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
        #(title_suffix, fn_suffix, variant_data)

        # For example, you might have a patient register
        # for Bugongi and Ruhiira health centers: 
        #(' Bugongi HC', '_BG', {'clinic_id': 13}),
        #(' Ruhiira HC', '_RH', {'clinic_id': 15}).
    ]

    # You should implement the generate method in a report
    # subclass.  This method creates the report and saves it
    # to the right place (probably static/reports/filename.format).
    # The return value is ignored.
    def generate(self, time_period, rformat, title, filepath, data):
        raise NotImplementedError(\
            _(u'Generate function not implemented.'))

    ####################
    # Unless you're an expert, you don't need to override
    # any of the rest of the methods in your subclass

    track_started = True
    abstract = True
    def run(self, *args, **kwargs):
        self._check_sanity()

        self._nightly = kwargs.get('nightly')
        if self._nightly is None:
            raise ValueError(_('No nightly value passed in'))
        self._time_period = kwargs.get('time_period')
        if self._time_period is None:
            raise ValueError(_('No time period value passed in'))

        if self._nightly:
            print "Running nightly (%s)" % self.formats
            self._dir = NIGHTLY_DIR
            self._run_nightly(*args, **kwargs)
        else:
            print "Running ondemand"
            self.run = self._run_ondemand
            self._dir = ONDEMAND_DIR
            self._run_ondemand(*args, **kwargs)

    def _run_nightly(self, *args, **kwargs):
        # Run report for all formats
        # ...and all variants

        # Save in static/nightly/basename_variant.format
        for rformat in self.formats:
            print "xRunning format %s" % rformat
            if len(self.variants) == 0:
                print "Finished only variant"
                self.generate(self._time_period,
                    rformat,
                    self.title,
                    self.get_filepath(rformat),
                    {})
                continue
            print "midloop"

            for variant in self.variants:
                print variant
                self.generate(self._time_period,
                    rformat,
                    self.title + variant[0],
                    self.get_filepath(rformat, variant[1]),
                    variant[2])

    def _check_sanity(self):
        if len(self.formats) == 0:
            raise ValueError(\
                _(u'This report has no formats specified.'))
        
        if self.title is None or self.filename is None:
            raise ValueError(\
                _(u'Report title or filename is unset.'))
 
    _generated_report = None
    def set_status(self, status):
        # Do stuff to update DB record here        
        pass

    def _run_ondemand(self, *args, **kwargs):
        # Run report for a single format and
        # a single variant for a single time
        # period
 
        # Check if a format was passed in
        rformat = kwargs.get('rformat')
        if rformat is None:
            raise ValueError('No report format requested.')
        if rformat not in self.formats:
            raise ValueError('Invalid report format requested.')

        # Check if a variant was passed in
        variant = kwargs.get('variant')
        if variant is None:
            variant = ('','',{})

        this_data = variant[2]
   
        # Create GeneratedReport record
        # and set to self._generated_report
        gr = GeneratedReport()
        gr.filename = self.get_filename(rformat, variant[1])
        gr.title = self.title
        gr.fileformat = rformat
        gr.period_title = self._time_period.title
        gr.variant_title = self.variant[0]
        gr.task_progress = 0
        gr.task_state = GeneratedReport.TASK_STATE_PENDING
        gr.started_at = datetime.now()
        gr.save()

        self._generated_report = gr

        # Generate the report
        self.generate(rformat, \
                    self._time_period,
                    self.title + variant[0],
                    self.get_filepath(rformat, variant[1]),
                    this_filepath,
                    this_data)

    def get_filepath(self, rformat, file_suffix = ''):
        if self.filename is None:
            raise ValueError(\
                _(u'Report filename is unset.'))

        task_pk = ''
        if not self._nightly: 
            if self._generated_report is None:
                raise ValueError(\
                    _('Generated report DB record is not set'))
            else:
                task_pk = "%d" % self._generated_report.pk

        return report_filepath(self._dir, \
            self.filename + file_suffix + task_pk, rformat)

    def get_filename(self, rformat, file_suffix=''):
        return self.filename+file_suffix_task_pk+'.'+rformat


