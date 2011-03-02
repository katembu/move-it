#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

from datetime import date, timedelta

from django.utils.translation import gettext as _
from django.db.models import Q

from ccdoc import Document, Table, Paragraph, \
    Text, Section, PageBreak

from childcount.models import CHW, Clinic, Patient
from childcount.models.reports import NutritionReport

from childcount.reports.utils import render_doc_to_file
from childcount.reports.report_framework import PrintedReport

class Report(PrintedReport):
    title = _(u"Malnutrition Report")
    filename = 'malnutrition'
    formats = ['pdf','html']

    def generate(self, rformat, title, filepath, data):
        doc = Document(title)
        doc.add_element(PageBreak())

        clinics = Clinic.objects.all()

        for clinic in clinics:
            doc.add_element(Section(clinic.name)) 
           
            t, t2 = self._malnutrition_table(clinic)
            doc.add_element(t)
            doc.add_element(t2)
            doc.add_element(PageBreak())

        return render_doc_to_file(filepath, rformat, doc)

    def _malnourished_by_clinic(self, clinic):
        under_fives = Patient\
            .objects\
            .filter(status=Patient.STATUS_ACTIVE,\
                clinic=clinic,\
                dob__gte=date.today()-timedelta(5*265.25))

        output = []
        no_report = []
        for u in under_fives:
            try:
                r = NutritionReport\
                    .objects\
                    .filter(encounter__chw__clinic=clinic,\
                        encounter__patient=u)\
                    .latest()
            except NutritionReport.DoesNotExist:
                no_report.append(u)
            else:
                if r.muac is None:
                    no_report.append(u)
                if r.muac is None and r.oedema == NutritionReport.OEDEMA_UNKOWN:
                    no_report.append(u)
                    continue

                if r.status != NutritionReport.STATUS_HEALTHY:
                    output.append(r)

        return (output, no_report)

    def _malnutrition_table(self, clinic):
        (malnourished, unknown) = self._malnourished_by_clinic(clinic)

        table = Table(7, \
            Text(_(u"Children U5 Flagged as Malnourished")))

        table.add_header_row([
            Text(_(u"Loc Code")),
            Text(_(u"Health ID")),
            Text(_(u"Name / Age")),
            Text(_(u"Last MUAC")),
            Text(_(u"MUAC Status")),
            Text(_(u"Od.")),
            Text(_(u"Household Head")),
        ])
        table.set_column_width(10, 0)
        table.set_column_width(10, 1)
        table.set_column_width(15, 3)
        table.set_column_width(15, 4)
        table.set_column_width(5, 5)
        for r in malnourished:
            (kid, nut) = (r.encounter.patient, r)

            muac_str = nut.encounter.encounter_date.strftime("%d-%b-%Y")
            if nut.status is not None:
                status_str = nut.verbose_state
            else:
                status_str = _(u'Unknown')

            if nut.muac:
                status_str += u' [%d]' % nut.muac
            else:
                status_str += _(u' -- No MUAC')
            oedema_str = nut.oedema 
                            
            table.add_row([
                Text(kid.location.code),
                Text(kid.health_id.upper()),
                Text(kid.full_name() + u" / " + kid.humanised_age()),
                Text(muac_str),
                Text(status_str),
                Text(oedema_str),
                Text(kid.household.full_name())
            ])
        
        table2 = Table(4, \
            Text(_(u"Children U5 without MUAC")))

        table2.add_header_row([
            Text(_(u"Loc Code")),
            Text(_(u"Health ID")),
            Text(_(u"Name / Age")),
            Text(_(u"Household Head")),
        ])
        table2.set_column_width(10, 0)
        table2.set_column_width(10, 1)
        for kid in unknown:
            table2.add_row([
                Text(kid.location.code),
                Text(kid.health_id.upper()),
                Text(kid.full_name() + u" / " + kid.humanised_age()),
                Text(kid.household.full_name())
            ])

        return (table, table2)



