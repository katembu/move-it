#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

# PMTCTAppointmentsPerWeek
from django.utils.translation import gettext as _
from childcount.reports.pmtct import appointments_per_week
from childcount.reports.utils import render_doc_to_file
from childcount.reports.report_framework import PrintedReport

class Report(PrintedReport):
    title = 'Appointments Per '
    filename = 'apts_per_'
    formats = ['pdf','xls','html']
    argvs = []
    variants = [(_('Month'), 'month', {'period_set': 'monthly'}), \
        (_('Week'), 'week', {'period_set': 'weekly'})]

    def generate(self, rformat, title, filepath, data):
        period_set = data['period_set']
        excel = False
        if rformat == 'xls':
            excel = True
        doc = appointments_per_week(title, period_set, excel)
        return render_doc_to_file(filepath, rformat, doc)
