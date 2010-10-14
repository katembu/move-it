#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

from operator import attrgetter
from itertools import groupby

from django.utils.translation import gettext_lazy as _, activate

from dateutil import relativedelta
from datetime import date, timedelta, datetime, time

from celery.decorators import periodic_task
from celery.task.schedules import crontab

from childcount.models import ImmunizationSchedule, ImmunizationNotification
from childcount.models import Patient, CHW
from childcount.models import FeverReport
from childcount.models import NutritionReport
from childcount.models import PregnancyReport
from childcount.models.ccreports import TheCHWReport

from childcount.reports import gen_operationalreport
from childcount.reports import gen_surveryreport

from alerts.utils import SmsAlert


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
                                        notify_on__lte=in_one_week, \
                                        patient__status=Patient.STATUS_ACTIVE)\
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

       #join dates together, then immunizations together ans send the SMS
            msg.append((imm, ' | '.join(schedules)))

        msg_to = ' '.join('[%s] %s' % (imm, dates) for imm, dates in msg)
        alert = SmsAlert(reporter=chw, msg=msg_to)
        sms_alert = alert.send()
        sms_alert.name = u"Immunization_reminder"
        sms_alert.save()


@periodic_task(run_every=crontab(hour=7, minute=0))
def daily_fever_reminder():
    '''
    Daily reminder of Fever followup cases after 48 hours.
    '''
    sdate = datetime.now() + relativedelta.relativedelta(days=-3)
    #sdate = datetime.combine(sdate.date(), time(7, 0))
    edate = datetime.now() + relativedelta.relativedelta(days=-2)
    #edate = datetime.combine(edate.date(), time(7, 0))
    frs = FeverReport.objects.filter(encounter__encounter_date__gte=sdate, \
                                encounter__encounter_date__lte=edate, \
                                rdt_result=FeverReport.RDT_POSITIVE, \
                            encounter__patient__status=Patient.STATUS_ACTIVE)\
                                .order_by('encounter__chw')
    current_reporter = None
    data = {}
    for report in frs:
        if not current_reporter or current_reporter != report.encounter.chw:
            current_reporter = report.encounter.chw
            data[current_reporter] = []
        data[current_reporter].append("%s +U F" % report.encounter.patient)

    for key in data:
        msg = ', ' . join(data.get(key))
        alert = SmsAlert(reporter=key, msg=msg)
        sms_alert = alert.send()
        sms_alert.name = u"fever_daily_reminder"
        sms_alert.save()


@periodic_task(run_every=crontab(hour=17, minute=30, day_of_week=0))
def weekly_muac_reminder():
    '''
    Weekly reminder of due Muac cases, 75 days or over since last chw visit
    '''
    data = {}
    for chw in TheCHWReport.objects.all():
        reminder_list = []
        for patient in chw.muac_list():
            try:
                nr = NutritionReport.objects.filter(encounter__chw=chw, \
                            encounter__patient=patient, \
                            encounter__patient__status=Patient.STATUS_ACTIVE)\
                            .latest()
            except NutritionReport.DoesNotExist:
                reminder_list.append(patient)
            else:
                today = datetime.today()
                delta_diff = today - nr.encounter.encounter_date
                days_since_last_muac = delta_diff.days
                if days_since_last_muac >= 75:
                    reminder_list.append(patient)
        data[chw] = reminder_list

    for chw in data:
        p_list = data.get(chw)
        x = 0
        y = 20
        done = False
        while not done:
            current_list = p_list[x:y]
            if not current_list:
                done = True
                break
            healthids = u' ' . join([i.health_id for i in current_list])
            msg = _(u"The following clients are due for +M: %(ids)s") % {
                    'ids': healthids}
            x += 20
            y += 20
            alert = SmsAlert(reporter=chw, msg=msg)
            sms_alert = alert.send()
            sms_alert.name = u"muac_weekly_reminder"
            sms_alert.save()


@periodic_task(run_every=crontab(hour=18, minute=0, day_of_week=0))
def weekly_initial_anc_visit_reminder():
    '''
    Initial ANC Visit weekly reminder
    '''
    pregs = PregnancyReport.objects.filter(anc_visits=0, \
                            encounter__patient__status=Patient.STATUS_ACTIVE)
    p_list = []
    alert_list = {}

    for prpt in pregs:
        if prpt.encounter.patient in p_list:
            continue
        patient = prpt.encounter.patient
        p_list.append(patient)
        try:
            rpt = PregnancyReport.objects.filter(anc_visits=0, \
                                        encounter__patient=patient).latest()
        except PregnancyReport.DoesNotExist:
            pass
        else:
            if not patient.chw in alert_list:
                alert_list[patient.chw] = []
            alert_list[patient.chw].append(patient)

    for chw in  alert_list:
        chw_list = alert_list.get(chw)
        w = ', ' . join(["%s %s" % (p.health_id.upper(), p.first_name) \
                                for p in chw_list])
        msg = _(u"Remind the following to go for their first clinic visit" \
                " %(list)s.") % {'list': w}
        alert = SmsAlert(reporter=chw, msg=msg)
        sms_alert = alert.send()
        sms_alert.name = u"weekly_initial_anc_visit_reminder"
        sms_alert.save()


@periodic_task(run_every=crontab(hour=18, minute=0, day_of_week=0))
def weekly_anc_visit_reminder():
    '''
    ANC Visit weekly reminder - 6 weeks have passed since last ANC visit
    '''
    pregs = PregnancyReport.objects.filter(weeks_since_anc__gt=6, \
                            encounter__patient__status=Patient.STATUS_ACTIVE)
    p_list = []
    alert_list = {}

    for prpt in pregs:
        if prpt.encounter.patient in p_list:
            continue
        patient = prpt.encounter.patient
        p_list.append(patient)
        try:
            rpt = PregnancyReport.objects.filter(weeks_since_anc__gt=6, \
                                        encounter__patient=patient).latest()
        except PregnancyReport.DoesNotExist:
            pass
        else:
            if not patient.chw in alert_list:
                alert_list[patient.chw] = []
            alert_list[patient.chw].append(patient)

    for chw in  alert_list:
        chw_list = alert_list.get(chw)
        w = ', ' . join(["%s %s" % (p.health_id.upper(), p.first_name) \
                                for p in chw_list])
        msg = _(u"Remind the following to go for a clinic visit" \
                " %(list)s.") % {'list': w}
        alert = SmsAlert(reporter=chw, msg=msg)
        sms_alert = alert.send()
        sms_alert.name = u"weekly_anc_visit_reminder"
        sms_alert.save()


# once a day: generating them every hour caused database to crash
@periodic_task(run_every=crontab(minute=0, hour=0))
def hourly_operationalreport():
    gen_operationalreport()

@periodic_task(run_every=crontab(minute=30, hour=0))
def hourly_surveyreport():
    gen_surveryreport()
