from celery.decorators import periodic_task
from celery.schedules import crontab

from reportgen.models import GeneratedReport
from reportgen.models import Report

from reportgen.utils import DISPLAY_REPORTS_MAX


@periodic_task(run_every=crontab(hour=11,minute=0))
def delete_old_reports():
    # Get oldest reports
    greps = GeneratedReport.objects.order_by('-started_at')[DISPLAY_REPORTS_MAX:]

    for g in greps:
        g.delete()



