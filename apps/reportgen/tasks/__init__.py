#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

__all__ = ('UtilizationReport',)

# This is the way we get the celery workers
# to register all of the ReportDefinition tasks
from reportgen.tasks import *

from celery.decorators import periodic_task
from celery.task.schedules import crontab

from reportgen.models import NightlyReport

# This is one big task now... we need
# to somehow split it up
@periodic_task(run_every=crontab(hour=0, minute=0))
def nightly_reports():
    n = NightlyReport.objects.all()

    results = []
    for record in n:
        print "[%s]" % record.report.title

        # Get the code that defines this report
        report_cls = record.report.get_definition()
        time_period = record.period()

        # Run the report
        results.append(report_cls.apply(kwargs=\
            {'time_period':time_period, 
            'nightly': record}))

    print ">> Done <<"
    return results


# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from celery.decorators import periodic_task
from celery.task.schedules import crontab

from reportgen.models import NightlyReport

# This is one big task now... we need
# to somehow split it up
@periodic_task(run_every=crontab(hour=0, minute=0))
def nightly_reports():
    n = NightlyReport.objects.all()

    results = []
    for record in n:
        print "[%s]" % record.report.title

        # Get the code that defines this report
        report_cls = record.report.get_definition()
        time_period = record.period()

        # Run the report
        results.append(report_cls.apply(kwargs=\
            {'time_period':time_period, 
            'nightly': record}))

    print ">> Done <<"
    return results


# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from celery.decorators import periodic_task
from celery.task.schedules import crontab

from reportgen.models import NightlyReport

# This is one big task now... we need
# to somehow split it up
@periodic_task(run_every=crontab(hour=0, minute=0))
def nightly_reports():
    n = NightlyReport.objects.all()

    results = []
    for record in n:
        print "[%s]" % record.report.title

        # Get the code that defines this report
        report_cls = record.report.get_definition()
        time_period = record.period()

        # Run the report
        results.append(report_cls.apply(kwargs=\
            {'time_period':time_period, 
            'nightly': record}))

    print ">> Done <<"
    return results


