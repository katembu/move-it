#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

import shutil
from datetime import datetime

from celery.task import Task
from celery.task.schedules import crontab

from django.utils.translation import gettext as _
from django.http import HttpResponseRedirect, HttpResponseNotFound

from reportgen.models import Report, GeneratedReport

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
    # Name of the file where this report is defined (e.g., Operational
    # if the file is Operational.py)
    classname = None
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

        if 'nightly' not in kwargs:
            raise ValueError(_('No nightly value passed in'))

        # nightly should be None or a NightlyReport object
        self._nightly = kwargs['nightly']

        # get Report object for this report
        try:
            self._report = Report.objects.get(classname=self.classname)
        except Report.DoesNotExist:
            raise DBConfigurationError(_("Could not find DB record "\
                "for a report with classname %s" % self.classname))

        self._time_period = kwargs.get('time_period')
        if self._time_period is None:
            raise ValueError(_('No time period value passed in'))

        if self._nightly is None:
            print "Running ondemand"
            self.run = self._run_ondemand
            self._dir = ONDEMAND_DIR
            self._run_ondemand(*args, **kwargs)
        else:
            print "Running nightly (%s)" % self.formats
            self._dir = NIGHTLY_DIR
            self._run_nightly(*args, **kwargs)

    def _run_nightly(self, *args, **kwargs):
        # Run report for all formats
        # ...and all variants

        # Save in static/nightly/basename_variant_rptpk.format
        for rformat in self.formats:
            print "Running format %s" % rformat
            if len(self.variants) == 0:
                print "Finished only variant"
                print "FP: %s" % self.get_filepath(None, rformat)
                self.generate(self._time_period,
                    rformat,
                    self.title,
                    self.get_filepath(None, rformat),
                    {})
                continue
            print "midloop"

            for variant in self.variants:
                print variant
                self.generate(self._time_period,
                    rformat,
                    self.title + variant[0],
                    self.get_filepath(variant[1], rformat),
                    variant[2])

    def _check_sanity(self):
        if len(self.formats) == 0:
            raise ValueError(\
                _(u'This report has no formats specified.'))
        
        if self.title is None or self.filename is None \
                or len(self.title) == 0 or len(self.filename) == 0:
            raise ValueError(\
                _(u'Report title or filename is unset.'))
 
    _generated_report = None
    def set_progress(self, progress):
        print "> Progress %d%%" % progress

        # Don't need status updates for nightly report
        if self._nightly: return

        self._generated_report.task_state = GeneratedReport.TASK_STATE_STARTED
        self._generated_report.task_progress = progress
        self._generated_report.save()

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
            variant = ('', None, {})

        this_data = variant[2]
   
        # Create GeneratedReport record
        # and set to self._generated_report
        gr = GeneratedReport()
        gr.filename = ''
        gr.title = self.title
        gr.report = self._report
        gr.fileformat = rformat
        gr.period_title = self._time_period.title
        gr.variant_title = variant[0]
        gr.task_progress = 0
        gr.task_state = GeneratedReport.TASK_STATE_PENDING
        gr.started_at = datetime.now()
        gr.save()

        # Once the PK is set, we can get the filename for 
        # the report
        self._generated_report = gr
        gr.filename = self.get_filename(variant[1], rformat)
        gr.save()


        # Generate the report
        self.generate(self._time_period,
                    rformat,
                    self.title + variant[0],
                    self.get_filepath(variant[1], rformat),
                    this_data)

    def on_success(self, retval, task_id, args, kwargs):
        if not self._generated_report: return

        self._generated_report.finished_at = datetime.now()
        self._generated_report.task_state = GeneratedReport.TASK_STATE_SUCCEEDED
        self._generated_report.task_progress = 100
        print "SUCCESS!!!"
        self._generated_report.save()
        
    def on_failure(self, exc, task_id, args, kwargs, einfo=None):
        print "FAILED!!!"

        if not self._generated_report: return 
        self._generated_report.finished_at = datetime.now()
        self._generated_report.task_state = GeneratedReport.TASK_STATE_FAILED
        self._generated_report.task_progress = 0
        
        if einfo is not None:
            self._generated_report.error_message = einfo.traceback
        self._generated_report.save()
        
    def get_filename(self, suffix, rformat):
        if self._nightly: 
            return self._nightly.get_filename(suffix, rformat)
        else:
            return self._generated_report.get_filename(suffix, rformat)

    def get_filepath(self, suffix, rformat):
        if self._nightly: 
            return self._nightly.get_filepath(suffix, rformat)
        else:
            return self._generated_report.get_filepath(suffix, rformat)

class DBConfigurationError(Exception):
    pass
