#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

import os.path
import shutil
import inspect
from datetime import datetime

from celery.task import Task
from celery.schedules import crontab

from django import db
from django.utils.translation import gettext as _
from django.http import HttpResponseRedirect, HttpResponseNotFound

from reportgen.models import Report, GeneratedReport, NightlyReport

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

    # A list of report variants
    # For example, you might have a patient register
    # for Bugongi and Ruhiira health centers: 
    variants = [
        #(title_suffix, fn_suffix, variant_data)

        #(' Bugongi HC', '_BG', {'clinic_id': 13}),
        #(' Ruhiira HC', '_RH', {'clinic_id': 15}).

        # Neither the title nor filename suffixes can be 
        # the empty string ""
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

    # Name of the file where this report is defined (e.g., Operational
    # if the file is Operational.py)
    @property
    def classname(self):
        return os.path.basename(inspect.getfile(self.generate))[0:-3]

    def run(self, *args, **kwargs):
        print "Args: %s" % str(args)
        print "Kwargs: %s" % str(kwargs)

        self.check_sanity()

        if 'nightly' not in kwargs:
            raise ValueError(_('No nightly value passed in'))

        # get Report object for this report
        try:
            kwargs['report'] = Report.objects.get(classname=self.classname)
        except Report.DoesNotExist:
            raise DBConfigurationError(_("Could not find DB record "\
                "for a report with classname %s" % self.classname))

        if 'time_period' not in kwargs:
            raise ValueError(_('No time period value passed in'))

        if kwargs['nightly'] is None:
            print "Running ondemand"
            kwargs['run'] = self._run_ondemand
            kwargs['dir'] = GeneratedReport.GENERATED_DIR
            self._run_ondemand(*args, **kwargs)
        else:
            print "Running nightly (%s)" % self.formats
            kwargs['dir'] = NightlyReport.NIGHTLY_DIR
            self._run_nightly(*args, **kwargs)

    def test(self, time_period, rformat):
        """
        Use this method to test your reports from
        the shell.
        """

        self._kwargs = {'nightly': 'Fake'}

        fname = "/tmp/test_%s.%s" % (self.filename, rformat)
        print "Saving as \"%s\"" % fname

        if self.variants:
            title = self.title + ": " + self.variants[0][0]
            data = self.variants[0][2]
        else:
            title = self.title
            data = {}


        return self.generate(time_period, rformat, title, fname, data)

    def _run_nightly(self, *args, **kwargs):
        print "[Nightly args] %s" % str(args)
        print "[Nightly kwargs] %s" % str(kwargs)

        self._kwargs = kwargs

        # Run report for all formats
        # ...and all variants

        # Save in static/nightly/basename_variant_rptpk.format
        for rformat in self.formats:
            print "Running format %s" % rformat
            if len(self.variants) == 0:
                print "Finished only variant"
                print "FP: %s" % self.get_filepath(kwargs, None, rformat)
                self.generate(kwargs['time_period'],
                    rformat,
                    self.title,
                    self.get_filepath(kwargs, None, rformat),
                    {})
                continue
            print "midloop"

            for variant in self.variants:
                print variant
                self.generate(kwargs['time_period'],
                    rformat,
                    self.title + variant[0],
                    self.get_filepath(kwargs, variant[1], rformat),
                    variant[2])

    def check_sanity(self):
        if len(self.formats) == 0:
            raise ValueError(\
                _(u'This report has no formats specified.'))
        
        if self.title is None or self.filename is None \
                or len(self.title) == 0 or len(self.filename) == 0:
            raise ValueError(\
                _(u'Report title or filename is unset.'))

    def set_progress(self, progress):
        # Clear query cache to keep Django from
        # eating all of the memory
        db.reset_queries()

        kwargs = self._kwargs

        print "> Progress %d%% (at %s)" % (progress, datetime.now())

        # Don't need status updates for nightly report
        if kwargs['nightly']: return
        print "++> %s" % repr(kwargs['nightly'])

        print "Working on saving"
        kwargs['generated_report'].task_state = GeneratedReport.TASK_STATE_STARTED
        kwargs['generated_report'].task_progress = progress
        kwargs['generated_report'].save()

    def _run_ondemand(self, *args, **kwargs):
        print "[Ondemand args] %s" % str(args)
        print "[Ondemand kwargs] %s" % str(kwargs)
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
        # Once the PK is set, we can get the filename for the report
        kwargs['generated_report'].filename = self.get_filename(kwargs, variant[1], rformat)
        kwargs['generated_report'].task_id = kwargs['task_id']
        kwargs['generated_report'].save()

        self._kwargs = kwargs

        # Generate the report
        self.generate(kwargs['time_period'],
                    rformat,
                    self.title + ": " + variant[0],
                    self.get_filepath(kwargs, variant[1], rformat),
                    this_data)

    def on_success(self, retval, task_id, args, kwargs):
        if 'generated_report' not in kwargs:
            print "Couldn't find generated report record"
            return

        kwargs['generated_report'].finished_at = datetime.now()
        kwargs['generated_report'].task_state = GeneratedReport.TASK_STATE_SUCCEEDED
        kwargs['generated_report'].task_progress = 100
        print "SUCCESS!!!"
        kwargs['generated_report'].save()
        
    def on_failure(self, exc, task_id, args, kwargs, einfo=None):
        print "FAILED!!!"
        print einfo

        print "Failed kwargs: (%s)" % (str(kwargs))
        if not kwargs.get('generated_report'):
            print "No generated report found"
            return 
        kwargs['generated_report'].finished_at = datetime.now()
        kwargs['generated_report'].task_state = GeneratedReport.TASK_STATE_FAILED
        kwargs['generated_report'].task_progress = 0
        
        if einfo is not None:
            kwargs['generated_report'].error_message = einfo.traceback
        kwargs['generated_report'].save()
        
    def get_filename(self, kwargs, suffix, rformat):
        if kwargs['nightly']: 
            return kwargs['nightly'].get_filename(suffix, rformat)
        else:
            return kwargs['generated_report'].get_filename(suffix, rformat)

    def get_filepath(self, kwargs, suffix, rformat):
        if kwargs['nightly']: 
            return kwargs['nightly'].get_filepath(suffix, rformat)
        else:
            return kwargs['generated_report'].get_filepath(suffix, rformat)

class DBConfigurationError(Exception):
    pass
