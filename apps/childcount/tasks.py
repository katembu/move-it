#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from operator import attrgetter
from itertools import groupby

from django.utils.translation import gettext_lazy as _, activate

from dateutil import relativedelta
from datetime import date, timedelta, datetime

from celery.decorators import periodic_task
from celery.task.schedules import crontab

from childcount.models import ImmunizationSchedule, ImmunizationNotification
from childcount.models import Patient, CHW
from childcount.utils import send_msg


@periodic_task(run_every=crontab(hour=16, minute=30, day_of_week=0))
def weekly_immunization_reminder():
    '''
    Send SMS to CHW to remind them their immunization appointments, using
    the format:
    [Immunization type] date: patient_id, patient_id | date: patient_id...
    '''

    # get this week appointements, grouped by CHW
    today = datetime.today()
    in_one_week = today + relativedelta.relativedelta(weeks=1)
    imms = ImmunizationNotification.objects.filter(notify_on__gte=today,
                                                  notify_on__lte=in_one_week)\
                                           .order_by('patient__chw')
    chws = groupby(imms, attrgetter('patient.chw'))

    # send an sms to each CHW
    for chw, imms in chws:
        msg = []

        # group notifications by immunization types
        imms = groupby(imms, attrgetter('immunization'))
        for imm, notifications in imms:

            # sort then group notifications by dates
            notifications = sorted(notifications, key=attrgetter('notify_on'))
            dates = groupby(notifications, attrgetter('notify_on'))

            # format id and dates
            schedules = []
            for date, ids in dates:
                ids = ', '.join(str(n.patient.health_id) for n in ids)
                schedules.append('%s: %s' % (date.strftime('%d-%m-%y'), ids))

       # join dates together, then immunizations together ans send the SMS
            msg.append((imm, ' | '.join(schedules)))

        send_msg(chw, ' '.join('[%s] %s' % (imm, dates) for imm, dates in msg))
