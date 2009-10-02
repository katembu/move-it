#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from datetime import date, datetime
from django.utils.translation import ugettext as _

from rapidsms import Message
from rapidsms.connection import *

from apps.reporters.models import *
from apps.rdtreporting.models import *

def get_lostItems():
    ''' return the Lost Items Location or create it '''

    try:
        lost    = Location.objects.get(code='lost')
    except:
        lost    = Location(name=_(u"Lost Items"), code='lost')
        lost.save()

    return lost
    

def alert_callback(router, *args, **kwargs):
    ''' Called by Scheduler App everyday at 4pm '''

    # get active reporters
    reporters   = list(Reporter.objects.filter(registered_self=True))

    # look for ones who haven't reported today
    today_reports= RDTReport.objects.filter(date=date.today())

    # remove reporters who have sent
    for report in today_reports:
        reporters.remove(report.reporter)

    # send alert to remaining ones
    for reporter in reporters:
        alert_reporter_noreport(reporter=reporter, day=date.today(), router=router)

    return True

def alert_reporter_noreport(reporter, day=date.today(), router=None):
    ''' sends an alert to a reporter '''

    real_backend = router.get_backend(reporter.connection().backend.slug)

    if real_backend:
        connection = Connection(real_backend, reporter.connection().identity)

        message = Message(connection=connection)
        message.text    = _(u"ALERT. You have not yet submitted your daily RDT report.")
        message.send()

        return True
    else:
        return False

def allow_me2u(message):
    ''' free2u App helper. Allow only registered users. '''

    try:
        if message.persistant_connection.reporter.registered_self:
            return True
        else:
            return False
    except:
        return False


        
