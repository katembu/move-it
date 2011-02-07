#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from childcount.reports.pmtct import pmtct_defaulters
from childcount.reports.utils import render_doc_to_file
from childcount.reports.report_framework import PrintedReport

class Report(PrintedReport):
    title = 'Defaulters Report'
    filename = 'pmtct_defaulters'
    formats = ['pdf','xls','html']
    argvs = []

    def generate(self, rformat, title, filepath, data):
        doc = pmtct_defaulters(title)
        return render_doc_to_file(filepath, rformat, doc)
