#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from datetime import date, datetime, timedelta
from django.utils.translation import ugettext as _

from apps.reporters.models import *
from apps.rdtreporting.models import *
from apps.tinystock.models import *
from models import *

def stock_for_location(location):
    ''' returns aggregated stock of location based on all reporters '''

    item    = Item.by_code('mrdt')
    stock   = 0
    reporters = Reporter.objects.filter(location=location)

    for reporter in reporters:
        try:
            store = StockItem.by_peer_item(peer=reporter, item=item)
            stock += store.quantity
        except:
            pass

    return stock

def stock_for_reporter(reporter):
    ''' return MRDT stock for a given reporter '''
    
    item    = Item.by_code('mrdt')
    try:
        stock   = StockItem.by_peer_item(peer=reporter, item=item).quantity
    except StockItem.DoesNotExist:
        stock   = 0

    return stock

def last_report(reporter):
    ''' returns last report from a reporter '''

    reports = RDTReport.objects.filter(reporter=reporter).order_by('-date')
    if reports.count() > 0:
        report  = list(reports)[-1]
    else:
        report  = None
    return report        

def report_for_location_date(location, day):
    ''' return the number of reports sent for a location on a day '''

    reporters = Reporter.objects.filter(location=location)
    reports = RDTReport.objects.filter(reporter__in=reporters, date=day)

    return reports.count()

def location_stats_dict(location):
    ''' return basic statistics for a location '''

    stock       = 0
    tested      = 0
    confirmed   = 0
    treatments  = 0
    used        = 0

    item        = Item.by_code('mrdt')
    reporters   = Reporter.objects.filter(location=location)
    
    reports     = RDTReport.objects.filter(reporter__in=reporters)
    for report in reports:
        tested += report.tested
        confirmed += report.confirmed
        treatments += report.treatments
        used += report.used

    '''
    for reporter in reporters:
        store = StockItem.by_peer_item(peer=reporter, item=item)
        stock += store.quantity
    '''

    return {'stock': stock, 'tested': tested, 'confirmed': confirmed, 'treatments': treatments, 'used': used}
