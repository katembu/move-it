#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import re
from datetime import date, datetime, timedelta
from django.utils.translation import ugettext as _
from rapidsms import Message
from rapidsms.connection import *
from apps.reporters.models import *
from models import *

def diseases_from_string(text):
    ''' returns a list of Disease with numbers build from SMS-syntax
    '''
    diseases= []
    
    # split different diseases declarations
    codes   = text.split(' ')

    for code in codes:
        if code == '': continue
        try:
            # extract values: <CODE><CASES#>+<DEATHS>
            extract = re.search('([a-zA-Z]+)([0-9]+)\+?([0-9]*)', code).groups()
            abbr    = extract[0].lower()
            cases   = int(extract[1])
            deaths  = 0 if extract[2].__len__() == 0 else int(extract[2])
        except:
            raise InvalidInput

        try:
            disease = Disease.by_code(abbr)
        except Disease.DoesNotExist:
            raise IncoherentValue(_(u'FAILED: %s is not a valid disease code.  Please try again.' % abbr))

        diseases.append({'disease': disease, 'cases': cases, 'deaths': deaths})

    return diseases

def allow_me2u(message):
    ''' free2u App helper. Allow only registered users. '''

    try:
        if message.persistant_connection.reporter.registered_self:
            return True
        else:
            return False
    except:
        return False

def cb_disease_alerts(router, *args, **kwargs):
    ''' Sends Alert messages to recipients

    Raised by Scheduler'''

    # retrieve unsent alerts
    alerts  = DiseaseAlert.objects.filter(status=DiseaseAlert.STATUS_STARTED)

    for alert in alerts:

        alert_msg   = _(u"ALERT. At least %(nbcases)s cases of %(disease)s in %(location)s during %(period)s") % {'nbcases': alert.value, 'disease': alert.trigger.disease, 'location': alert.trigger.location, 'period': alert.period}

        for reporter in list(alert.recipients.all()):

            try:
                real_backend = router.get_backend(reporter.connection().backend.slug)
                if real_backend:
                    connection  = Connection(real_backend, reporter.connection().identity)
                    message     = Message(connection=connection)
                    message.text= alert_msg
                    message.send()
            except Exception, e:
                print _(u"Can't send alert to %(rec)s: %(err)s") % {'rec': reporter, 'err': e}
                pass

        # change alert status
        alert.status    = DiseaseAlert.STATUS_COMPLETED
        alert.save()

def report_completed_alerts(router, report):
    ''' send alerts about a completed report. '''

    # verify report is done
    if not report.status == EpidemiologicalReport.STATUS_COMPLETED:
        return False

    # get sub districts
    targets = []
    for ancestor in report.clinic.ancestors():
        if ancestor.type.name.lower().__contains__('health sub district'): targets.append(ancestor)

    # get reporters
    recipients  = []
    reporters   = Reporter.objects.filter(registered_self=True, location__in=targets)
    for reporter in reporters:
        if ReporterGroup.objects.get(title='weekly_completion_alerts') in reporter.groups.only(): recipients.append(reporter)

    # send alerts
    alert_msg   = _(u"%(clinic)s has fully reported %(period)s %(title)s on %(date)s.") % {'clinic': report.clinic, 'period': report.period, 'title': report.TITLE, 'date': report.completed_on.strftime("%d/%m/%y %H:%M")}

    for recipient in recipients:
        try:
            real_backend = router.get_backend(recipient.connection().backend.slug)
            if real_backend:
                connection  = Connection(real_backend, recipient.connection().identity)
                message     = Message(connection=connection)
                message.text= alert_msg
                message.send()
        except Exception, e:
            print _(u"Can't send alert to %(rec)s: %(err)s") % {'rec': recipient, 'err': e}
            pass
  

