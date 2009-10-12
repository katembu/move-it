#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from datetime import datetime, date

from django.db import IntegrityError

from models import *

def parseday(day):

    try:
        d = int(day[:2])
        m = int(day[2:][:2])
        y = int('20'+day[4:][:2])

        return y, m, d

    except:
        return None

def record_mrdt(reporter, tested, confirmed, treatments, used, day=date.today(), overwrite=False):
    ''' records a day of MRDT tests '''

    # verify amounts integrity

    # tested is > confirmed, treatments
    if tested < confirmed or tested < treatments:
        raise IncoherentValue

    # used >= tested
    if used < tested:
        raise IncoherentValue

    # treatments <= confirmed
    if treatments > confirmed:
        raise IncoherentValue

    # check reporter
    if not isinstance(reporter, Reporter):
        raise UnknownReporter
    
    if not reporter.registered_self:
        raise UnknownReporter

    # check date
    if isinstance(day, str):
        day = date(*parseday(day))

    if not isinstance(day, date):
        raise ErroneousDate

    # backup existing (then delete) if exists and overwrite=True
    overwritten = False
    existings   = RDTReport.objects.filter(reporter=reporter, date=day)

    if existings.count() > 0 and not overwrite:
        raise DuplicateReport
    elif existings.count() > 0 and overwrite:
        existing    = existings.latest('date_posted')
        backup      = ErroneousRDTReport.from_rdt(existing)
        existing.delete()
        overwritten = True

    # save the report
    try:
        report  = RDTReport(reporter=reporter, tested=tested, confirmed=confirmed, treatments=treatments, used=used, date=day)
        report.save()
    except IntegrityError:
        raise DuplicateReport
    except:
        raise

    return report, overwritten

# new, full version
def record_mrdt_full(reporter, tested, confirmed, act, cqsp, quinine, antibiopos, antibioneg, under_five, day=date.today(), overwrite=False):
    ''' records a day of MRDT tests '''

    # verify amounts integrity

    # tested is > confirmed, treatments
    if tested < confirmed or tested < (act or cqsp or quinine or antibiopos or antibioneg):
        raise IncoherentValue

    # all treatments (+) <= confirmed
    if (act + cqsp + quinine + antibiopos) > confirmed:
        raise IncoherentValue

    # all treatments <= tested
    if (act + cqsp + quinine + antibiopos) + antibioneg > tested:
        raise IncoherentValue

    # check reporter
    if not isinstance(reporter, Reporter):
        raise UnknownReporter
    
    if not reporter.registered_self:
        raise UnknownReporter

    # check date
    if isinstance(day, str):
        day = date(*parseday(day))

    if not isinstance(day, date):
        raise ErroneousDate

    # backup existing (then delete) if exists and overwrite=True
    overwritten = False
    existings   = FullRDTReport.objects.filter(reporter=reporter, date=day)

    if existings.count() > 0 and not overwrite:
        raise DuplicateReport
    elif existings.count() > 0 and overwrite:
        existing    = existings.latest('date_posted')
        backup      = ErroneousFullRDTReport.from_rdt(existing)
        existing.delete()
        overwritten = True

    # save the report
    try:
        report  = FullRDTReport(reporter=reporter, tested=tested, confirmed=confirmed, act=act, cqsp=cqsp, quinine=quinine, antibiopos=antibiopos, antibioneg=antibioneg, under_five=under_five, date=day)
        report.save()
    except IntegrityError:
        raise DuplicateReport
    except:
        raise

    return report, overwritten

def record_alert(reporter, day):
    ''' record a sent alert to a reporter '''

    # check reporter
    if not isinstance(reporter, Reporter):
        raise UnknownReporter
    
    if not reporter.registered_self:
        raise UnknownReporter

    # check date
    if isinstance(day, str):
        day = date(*parseday(day))

    if not isinstance(day, date):
        raise ErroneousDate

    alert   = RDTAlert(reporter=reporter, date=day)
    alert.save()

    return alert

    


    
