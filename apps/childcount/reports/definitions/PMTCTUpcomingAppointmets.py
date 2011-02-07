#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from childcount.reports.pmtct import upcoming_appointments
from childcount.reports.utils import render_doc_to_file
from childcount.reports.report_framework import PrintedReport


class Report(PrintedReport):
    title = 'Upcoming Appointments'
    filename = 'pmtct_upcoming_appointments'
    formats = ['pdf', 'html']
    argvs = []

    def generate(self, rformat, title, filepath, data):
        doc = upcoming_appointments(title)
        return render_doc_to_file(filepath, rformat, doc)
