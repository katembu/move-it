#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: diarra

from datetime import datetime, date

from django.utils.translation import gettext_lazy as _

from ccdoc import Document, Table, Paragraph, Text, Section

from childcount.models import Patient, CHW
from locations.models import Location

from childcount.reports.utils import render_doc_to_file
from childcount.reports.report_framework import PrintedReport
from childcount.models.reports import (PregnancyReport, FeverReport,
                                       NutritionReport)


def _(text):
    """ short circuits the translation as not supported by CCdoc
    """
    return text


def date_under_five():
    """ Returns the date reduced by five years """

    today = date.today()
    date_under_five = date(today.year - 5, today.month, today.day)
    return date_under_five


def rdt(health_id):
    """ RDT test status

        Params:
            * health_id """
    try:
        rdt = FeverReport.objects.\
            get(encounter__patient__health_id=health_id).rdt_result
    except FeverReport.DoesNotExist:
        rdt = '-'

    return rdt


class Report(PrintedReport):
    title = 'PatientReport'
    filename = 'PatientReport'
    formats = ['html', 'pdf', 'xls']
    argvs = []

    def generate(self, rformat, title, filepath, data):
        doc = Document(title)
        d_today = datetime.today()
        for chw in CHW.objects.all():
            d = date_under_five()

            children = Patient.objects.filter(chw=chw.id, dob__gt=d)[:5]

            if children:
                table1 = Table(11)
                table1.add_header_row([
                    Text((u'#')),
                    Text(_(u'Name')),
                    Text(_(u'Gender')),
                    Text(_(u'Age')),
                    Text(_(u"Mother's name")),
                    Text(_(u'Location code')),
                    Text(_(u'RDT+ (past 6mo)')),
                    Text(_(u'MUAC (+/-)')),
                    Text(_(u'Last Visit')),
                    Text(_(u'PID')),
                    Text(_(u'Instructions'))
                    ])

                doc.add_element(Paragraph("%s clinic: %s " %\
                                        (chw.clinic, chw.full_name())))
                doc.add_element(Paragraph("CHILDREN"))

                num = 0

                for child in children:
                    num += 1

                    # RDT test status
                    rdt_result = rdt(child.health_id)

                    # muac
                    try:
                        muac = NutritionReport.objects.\
                            get(encounter__patient__health_id=child.\
                                health_id).muac
                    except NutritionReport.DoesNotExist:
                        muac = '-'

                    if child.mother:
                        mother = child.mother.full_name()
                    else:
                        mother = '-'

                    table1.add_row([
                        Text(num),
                        Text(child.full_name()),
                        Text(child.gender),
                        Text(child.humanised_age()),
                        Text(mother),
                        Text(child.location.code),
                        Text(rdt_result),
                        Text(muac),
                        Text((d_today - child.updated_on).days),
                        Text(child.health_id),
                        Text('')
                        ])

                doc.add_element(table1)

            pregnant_women =\
                   PregnancyReport.objects.filter(encounter__chw=chw.id)[:5]

            if pregnant_women:
                table2 = Table(11)
                table2.add_header_row([
                    Text((u'#')),
                    Text(_(u'Name')),
                    Text(_(u'Location')),
                    Text(_(u'Age')),
                    Text(_(u'Pregnancy')),
                    Text(_(u'# children')),
                    Text(_(u'RDT+ (past 6 mo)')),
                    Text(_(u'Last Visit')),
                    Text(_(u'Next ANC')),
                    Text(_(u'PID')),
                    Text(_(u'Instructions'))
                    ])

                doc.add_element(Paragraph("%s clinic: %s " %\
                                        (chw.clinic, chw.full_name())))
                doc.add_element(Paragraph("PREGNANT WOMEN"))

                num = 0

                for woman in pregnant_women:
                    num += 1

                    # RDT test status
                    rdt_result = rdt(woman.pregnancyreport.encounter\
                                          .patient.health_id)

                    table2.add_row([
                    Text(num),
                    Text(str(woman.pregnancyreport.encounter\
                                                  .patient.full_name())),
                    Text(woman.pregnancyreport.encounter\
                                              .patient.location.name),
                    Text(woman.pregnancyreport.encounter\
                                              .patient.humanised_age()),
                    Text(woman.pregnancy_month),
                    Text(woman.pregnancyreport.encounter.patient.child \
                                              .all().count()),
                    Text(rdt_result),
                    Text((d_today - woman.pregnancyreport.encounter.patient.updated_on).days),
                    Text(''),
                    Text(woman.pregnancyreport.encounter.patient.health_id),
                    Text('')
                    ])

                doc.add_element(table2)

            women = Patient.objects.\
                            filter(chw=chw.id, gender='F', dob__gt=d)[:5]

            if women:
                table3 = Table(9)
                table3.add_header_row([
                    Text((u'#')),
                    Text(_(u'Name')),
                    Text(_(u'Age')),
                    Text(_(u'Location code')),
                    Text(_(u'# children')),
                    Text(_(u'RDT+ (past 6 mo)')),
                    Text(_(u'Last Visit')),
                    Text(_(u'PID#')),
                    Text(_(u'Instructions'))
                    ])

                doc.add_element(Paragraph("%s clinic: %s " %\
                                        (chw.clinic, chw.full_name())))
                doc.add_element(Paragraph("WOMEN"))

                num = 0

                for woman in women:
                    num += 1

                    # RDT test status
                    rdt_result = rdt(woman.health_id)

                    table3.add_row([
                    Text(num),
                    Text(woman.full_name()),
                    Text(woman.humanised_age()),
                    Text(woman.location.code),
                    Text(woman.child.all().count()),
                    Text(rdt_result),
                    Text((d_today - woman.updated_on).days),
                    Text(woman.health_id),
                    Text('')
                    ])

                doc.add_element(table3)

        return render_doc_to_file(filepath, rformat, doc)
