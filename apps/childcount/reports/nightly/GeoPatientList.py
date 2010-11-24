#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

from django.utils.translation import gettext_lazy as _

from ccdoc import Document, Table, Paragraph, Text, Section

from childcount.models import Patient
from locations.models import Location

from childcount.reports.utils import render_doc_to_file
from childcount.reports.report_framework import PrintedReport


class Report(PrintedReport):
    title = 'Patient List by Location'
    filename = 'geo_patient_list'
    formats = ['html','pdf','xls']
    argvs = []
    order = 1

    def generate(self, rformat, **kwargs):
        report_title = (u'Patient List by Location')
        doc = Document(report_title)
        doc.add_element(Paragraph( \
            u'Sorted by location and HH first name. \
            HH names are in bold.'))
        
        table = Table(4)
        table.add_header_row([
            Text(_(u'Location')),
            Text(_(u'HH Health ID')),
            Text(_(u'Health ID')),
            Text(_(u'Name'))
            ])

        # Get all top-level locations (those without parents)
        top = Location.objects.filter(parent__isnull=True).order_by('name')
        for t in top:
            # Process children
            self._patient_list_geo_recurse(t, [], table)

        doc.add_element(table)
        return render_doc_to_file(self.get_filename(), rformat, doc)

    def _patient_list_geo_recurse(self, loc, parents, table):
        parents.append(loc)
        locstr = u''
        for i, p in enumerate(parents):
            locstr += unicode(p) + u' [' + unicode(p.type) + u']'
            if i+1 != len(parents):
                locstr += u' > '

        hhs = Patient.objects.filter(chw__clinic__location_ptr = loc).order_by('first_name')
        for hh in hhs:
            if not hh.is_head_of_household():
                continue

            _add_patient_to_table(table, locstr, hh)
            for p in Patient.objects.filter(household = hh):
                if not p.is_head_of_household():
                    _add_patient_to_table(table, locstr, p)

        # Recursively run on all children locations
        for c in loc.children.all().order_by('name'):
            _patient_list_geo_recurse(c, parents, table)
        parents.pop()

    def _add_patient_to_table(table, locstr, patient):
        b = patient.is_head_of_household()
        table.add_row([
            Text(locstr),
            Text(patient.household.health_id.upper(), bold=b),
            Text(patient.health_id.upper(), bold=b),
            Text(patient.full_name(), bold=b)
        ])
