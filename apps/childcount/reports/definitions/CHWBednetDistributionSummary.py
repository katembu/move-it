#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: tief

from datetime import date

from django.utils.translation import gettext as _
from django.db.models import Sum

from ccdoc import Document, Table, Text, Section, Paragraph

from childcount.models import BednetStock, DistributionPoints
from childcount.models import BednetIssuedReport

from childcount.reports.utils import render_doc_to_file
from childcount.reports.report_framework import PrintedReport

class Report(PrintedReport):
    title = 'CHW Bednet Distribution Summary: '
    filename = 'dp'
    formats = ['html', 'pdf']
    argvs = []
    variants = map(lambda dp: \
        (dp.location.__unicode__(), '_' + dp.location.code, {'dp_pk': dp.pk}),
        DistributionPoints.objects.all())

    def generate(self, rformat, title, filepath, data):
        # Make sure that user passed in a distribution point 
        if 'dp_pk' not in data:
            raise ValueError('No distribution point index passed to report')
        dp_pk = data['dp_pk']
        dp = DistributionPoints.objects.get(pk=dp_pk)
        title = u'CHW Bednet Distribution Summary: %s' % dp.location
        doc = Document(title, landscape=True, stick_sections=True)
        try:
            dp = DistributionPoints.objects.get(location=dp.location)
        except DistributionPoints.DoesNotExist:
            return True
        for bs in BednetStock.objects.filter(location=dp.location):
            txt = u'%s, Starting Point: %s; End Point: %s; Issued: %s.' % \
                (bs.created_on.strftime('%d-%b-%Y'),
                bs.start_point, bs.end_point, (bs.start_point - bs.end_point))
            doc.add_element(Paragraph(txt))
            table = self._create_chw_table()
            chws = dp.chw.all()
            self._add_total_to_table(table, chws, bs.created_on.date())
            for chw in chws:
                self._add_chw_to_table(table, chw, bs.created_on.date())
            doc.add_element(table)
        if BednetStock.objects.filter(location=dp.location):
            bs = BednetStock.objects.filter(location=dp.location)[0]
            txt = u'Nets issued since %s' % \
                (bs.created_on.strftime('%d-%b-%Y'))
            doc.add_element(Paragraph(txt))
            table = self._create_chw_table()
            chws = dp.chw.all()
            self._add_total_to_table(table, chws, bs.created_on.date(), True)
            for chw in chws:
                self._add_chw_to_table(table, chw, bs.created_on.date(), True)
            doc.add_element(table)

        return render_doc_to_file(filepath, rformat, doc)

    def _create_chw_table(self):
        table = Table(2)
        table.add_header_row([
            Text(_(u'CHW')),
            Text(_(u'# Nets Issued'))
            ])
        # column alignments
        table.set_alignment(Table.ALIGN_LEFT, column=0)
        table.set_alignment(Table.ALIGN_LEFT, column=1)
        # column sizings
        table.set_column_width(20, column=0)

        return table

    def _add_chw_to_table(self, table, chw, dod, after=False):
        """ add chw to table """
        is_bold = False
        if not after:
            inets = BednetIssuedReport.objects\
                    .filter(encounter__encounter_date__day=dod.day,
                    encounter__encounter_date__month=dod.month,
                    encounter__encounter_date__year=dod.year,
                    encounter__chw=chw)\
                    .aggregate(dc=Sum('bednet_received'))
        else:
            inets = BednetIssuedReport.objects\
                    .filter(encounter__encounter_date__gte=dod,
                    encounter__chw=chw)\
                    .aggregate(dc=Sum('bednet_received'))
        if inets['dc']:
            count = inets['dc']
        else:
            count = 0
        table.add_row([
            Text(chw.__unicode__(), bold=is_bold),
            Text(count, bold=is_bold)])

    def _add_total_to_table(self, table, chws, dod, after=False):
        """ add chw to table """
        is_bold = False
        total = 0
        for chw in chws:
            if not after:
                inets = BednetIssuedReport.objects\
                        .filter(encounter__encounter_date__day=dod.day,
                        encounter__encounter_date__month=dod.month,
                        encounter__encounter_date__year=dod.year,
                        encounter__chw=chw)\
                        .aggregate(dc=Sum('bednet_received'))
            else:
                inets = BednetIssuedReport.objects\
                        .filter(encounter__encounter_date__gte=dod,
                        encounter__chw=chw)\
                        .aggregate(dc=Sum('bednet_received'))
            if inets['dc']:
                count = inets['dc']
            else:
                count = 0
            total += count
        table.add_row([
            Text(u'Total Count', bold=is_bold),
            Text(total, bold=is_bold)])
