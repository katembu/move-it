#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

"""Tasks
"""

from operator import attrgetter
from itertools import groupby

from django.utils.translation import ugettext_lazy as _, activate

from dateutil import relativedelta
from datetime import date, timedelta, datetime, time
from celery.decorators import periodic_task
from celery.schedules import crontab

from alerts.utils import SmsAlert

class NowPeriod(object):
    end = datetime.now()
    start = datetime.now() + timedelta(days=-30)
    title = "Past 30 Days"

#@periodic_task(run_every=crontab(hour="*", minute="*", day_of_week="*"))
@periodic_task(run_every=crontab(hour="*", minute="*", day_of_week="*"))
def weekly_immunization_reminder():
    print "hello"


def send_reminder():
    groups = ("registrar")

    reporters = Reporter.objects.filter(user_ptr__groups__name__in=groups)

    msg = _("MOVE-IT system is up now. You can now start sending text alerts")

    for r in reporters:
        msg2 = ', '.join([x.code for x in r.chw.assigned_location.all()])
        alert = SmsAlert(reporter=r, msg=msg)
        sms_alert = alert.send()

        sms_alert.name = "MOVE-IT Reminder"
        sms_alert.save()
