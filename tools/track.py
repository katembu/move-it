#!/usr/bin/python

from datetime import date, timedelta

from childcount.models.ccreports import TheCHWReport
from childcount.models.reports import NutritionReport
from childcount.models import Patient
from childcount.reports.utils import MonthlyPeriodSet

def go():
    chws = TheCHWReport.objects.all()

    start = date(2010,9,1)
    end = date(2011,3,1)
    increment = timedelta(15)

    periods = []
    cur_date = start
    data = {}
    for chw in chws:
        data[chw.pk] = []

    while cur_date < end:
        periods.append(cur_date)
        for chw in chws:
            print (chw, cur_date)
            (n,d) = chw.fraction_ontime_muac(cur_date)
            row = {'raw': (n,d)}
            row['muacs'] = NutritionReport\
                .objects\
                .filter(encounter__chw__pk=chw.pk,
                    encounter__patient__status=Patient.STATUS_ACTIVE,
                    encounter__encounter_date__lte=cur_date,
                    encounter__encounter_date__gte=cur_date-timedelta(30))\
                .count()

            if d == 0: 
                row['frac'] = 0.0
            else:
                row['frac'] = 100.0 * float(n)/d

            data[chw.pk].append(row)
        cur_date += increment

    print "\n\n\n",
    print "Name,",
    for p in periods:
        print "%s," % p,
    print "\n",

    for pk in data.keys():
        print "\"%s\"," % TheCHWReport.objects.get(pk=pk).full_name(),
        for p in data[pk]:
            print "%0.2f," % p['frac'],
        print "\n",
    print "\n"

    print "\n\n\n",
    print "Name,",
    for p in periods:
        print "%s," % p,
    print "\n",

    for pk in data.keys():
        print "\"%s\"," % TheCHWReport.objects.get(pk=pk).full_name(),
        for p in data[pk]:
            print "%d," % p['muacs'],
        print "\n",
    print "\n"

