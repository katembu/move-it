#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import copy

from django.utils.translation import gettext_lazy as _
from django.db.models import Sum

from ccdoc import Document, Table, Text, Section

from locations.models import Location
from childcount.models import CHW
from childcount.models import BednetStock, DistributionPoints
from childcount.models import BednetIssuedReport, BedNetReport

from childcount.reports.utils import render_doc_to_file
from childcount.reports.report_framework import PrintedReport


class Report(PrintedReport):
    title = u'Bednet Summary Report'
    filename = 'bn_summary'
    formats = ['pdf', 'xls', 'html']

    def generate(self, rformat, title, filepath, data):
        doc = Document(title, landscape=True, stick_sections=True)

        # Produce the report
        locations = Location.objects.all()
        table = self._create_netsummary_table()
        for location in locations:
            self._add_report_to_table(table, location)
        doc.add_element(table)

        for location in locations:
            if CHW.objects.filter(location=location).count():
                doc.add_element(Section(location.__unicode__()))
                table = self._create_netsummary_table()
                for chw in CHW.objects.filter(location=location):
                    self._add_chw_report_to_table(table, chw)
                doc.add_element(table)

        return render_doc_to_file(filepath, rformat, doc)

    def _create_netsummary_table(self):
        table = Table(6)
        table.add_header_row([
            Text(u'%s' % _(u'Location')),
            Text(u'%s' % _(u'# Sleeping Sites')),
            Text(u'%s' % _(u'# Functioning Nets')),
            Text(u'%s' % _(u'# Required Nets B4')),
            Text(u'%s' % _(u'# Nets Issued')),
            Text(u'%s' % _(u'# Required Nets After D'))])

        return table

    def _add_report_to_table(self, table, location):
        bdnt_issued = BednetIssuedReport.objects\
            .filter(encounter__patient__location=location)\
            .aggregate(stotal=Sum('bednet_received'))['stotal']
        if not bdnt_issued:
            bdnt_issued = 0
        nets = BedNetReport.objects\
            .filter(encounter__patient__location=location)\
            .aggregate(dsites=Sum('sleeping_sites'),
            dfuncnets=Sum('function_nets'))
        if not nets['dsites'] and not nets['dfuncnets']:
            return
        try:
            required = nets['dsites'] - nets['dfuncnets'] - bdnt_issued
        except:
            required = 0
        try:
            orequired = nets['dsites'] - nets['dfuncnets']
        except:
            orequired = 0
        is_bold = False
        table.add_row([
            Text(location.__unicode__(), bold=is_bold),
            Text(nets['dsites'], bold=is_bold),
            Text(nets['dfuncnets'], bold=is_bold),
            Text(orequired, bold=is_bold),
            Text(bdnt_issued, bold=is_bold),
            Text(required, bold=is_bold)])

    def _add_chw_report_to_table(self, table, chw):
        bdnt_issued = BednetIssuedReport.objects\
            .filter(encounter__patient__chw=chw)\
            .aggregate(stotal=Sum('bednet_received'))['stotal']
        if not bdnt_issued:
            bdnt_issued = 0
        nets = BedNetReport.objects\
            .filter(encounter__patient__chw=chw)\
            .aggregate(dsites=Sum('sleeping_sites'),
            dfuncnets=Sum('function_nets'))
        if not nets['dsites'] and not nets['dfuncnets']:
            return
        try:
            required = nets['dsites'] - nets['dfuncnets'] - bdnt_issued
        except:
            required = 0
        try:
            orequired = nets['dsites'] - nets['dfuncnets']
        except:
            orequired = 0
        is_bold = False
        table.add_row([
            Text(chw.__unicode__(), bold=is_bold),
            Text(nets['dsites'], bold=is_bold),
            Text(nets['dfuncnets'], bold=is_bold),
            Text(orequired, bold=is_bold),
            Text(bdnt_issued, bold=is_bold),
            Text(required, bold=is_bold)])
