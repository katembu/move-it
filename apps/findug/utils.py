#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from datetime import date, datetime, timedelta
from django.utils.translation import ugettext as _

from rapidsms import Message
from rapidsms.connection import *

from apps.reporters.models import *
from apps.rdtreporting.models import *
from apps.tinystock.models import *
from models import *

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

def stock_alert_callback(router, *args, **kwargs):
    ''' check everybody's stock and send alert if low '''

    # get low level
    try:
        low = Configuration.objects.get(id=1).low_stock_level
    except:
        low = 5

    mrdt    = Item.by_code('mrdt')
    stocks  = StockItem.objects.filter(item=mrdt, quantity__lt=low)

    for stock in stocks:

        reporter    = stock.peer

        # skip clinic
        if not reporter.__class__ == Reporter:
            continue

        # skip inactives
        if not reporter.registered_self:
            continue

        # skip alerted ones
        if RDTStockAlert.objects.filter(reporter=reporter, status=RDTStockAlert.STATUS_SENT).count() > 0:
            continue
    
        real_backend = router.get_backend(reporter.connection().backend.slug)

        if real_backend:
            connection = Connection(real_backend, reporter.connection().identity)

            # create alert object
            alert   = RDTStockAlert(reporter=reporter, quantity=stock.quantity)

            message = Message(connection=connection)
            message.text    = _(u"ALERT. Your %(item)s stock is low (%(qty)s<%(low)s). Please refill.") % {'item': mrdt, 'qty': stock.quantity, 'low': low}
            message.send()

            alert.save()


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





