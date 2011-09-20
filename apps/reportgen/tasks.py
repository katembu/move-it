from celery.decorators import periodic_task
from celery.schedules import crontab

from reportgen.models import GeneratedReport
from reportgen.models import Report

from reportgen.utils import DISPLAY_REPORTS_MAX

from reportgen.ccgdata.utils import update_vital_events_report
from reportgen.ccgdata.utils import update_13Wvital_events_report


@periodic_task(run_every=crontab(hour=11, minute=0))
def delete_old_reports():
    # Get oldest reports
    greps = GeneratedReport.objects.order_by('-started_at')[DISPLAY_REPORTS_MAX:]

    for g in greps:
        g.delete()


@periodic_task(run_every=crontab(hour=13, minute=0))
def update_google_vitalevents_reports_spreadsheet():
    # Update Google Vital events reports
    update_vital_events_report()


@periodic_task(run_every=crontab(hour=13, minute=30))
def update_google_113Wvitalevents_reports_spreadsheet():
    # Update Google Vital events reports
    update_13Wvital_events_report()
