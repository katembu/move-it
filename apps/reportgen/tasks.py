from celery.decorators import periodic_task
from celery.schedules import crontab

from reportgen.models import NightlyReport
from reportgen.models import GeneratedReport
from reportgen.models import Report

from reportgen.utils import DISPLAY_REPORTS_MAX

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

@periodic_task(run_every=crontab(hour=11,minute=0))
def delete_old_reports():
    # Get oldest reports
    greps = GeneratedReport.objects.order_by('-started_at')[DISPLAY_REPORTS_MAX:]

    for g in greps:
        g.delete()



