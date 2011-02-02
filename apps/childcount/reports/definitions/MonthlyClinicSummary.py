#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import csv
from datetime import datetime

from django.utils.translation import gettext_lazy as _

from childcount.models.ccreports import ClinicReport
from childcount.reports.report_framework import PrintedReport

class Report(PrintedReport):
    title = 'Monthly Clinic Summary'
    filename = 'monthly_clinic_summary'
    formats = ['csv']

    def generate(self, rformat, title, filepath, data):
        '''
        Monthly clinic summary
        '''
        if rformat != 'csv':
            raise NotImplementedError('Can only generate CSV for monthly summary')

        start_date = datetime(year=2010, month=1, day=1)
        current_date = datetime.today()

        f = open(filepath, 'w')

        dw = csv.DictWriter(f, ['clinic', 'month', 'rdt', 'positive_rdt', \
                                            'nutrition', 'malnutrition'])
        for clinic in ClinicReport.objects.all():
            i = 1
            header = {'clinic': _(u"Clinic/Health Facility"), \
                        'month': _(u"Month"), \
                        'rdt': _(u"# of Fever Report(RDT)"), \
                        'positive_rdt': _(u"# Positive Fever Report"), \
                        'nutrition': _(u"# Nutrition Report"), \
                        'malnutrition': _(u"# Malnourished")}
            dw.writerow(header)
            while i <= 12:
                data = clinic.monthly_summary(i, start_date.year)
                dw.writerow(data)
                i += 1
        f.close()
        return True
