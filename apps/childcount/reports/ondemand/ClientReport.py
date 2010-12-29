#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: diarra

from datetime import datetime, date

from django.utils.translation import gettext as _

from ccdoc import Document, Table, Paragraph, Text, Section, PageBreak

from childcount.models import Patient, CHW
from childcount.reports.utils import render_doc_to_file
from childcount.reports.report_framework import PrintedReport
from childcount.models.reports import (PregnancyReport, FeverReport,
                                       NutritionReport)


def date_under_five():
    """ Returns the date reduced by five years """

    today = date.today()
    date_under_five = date(today.year - 5, today.month, today.day)
    return date_under_five


def birth_date(num):
    """ Returns the date reduced by five years """
    today = date.today()
    remaining = 9 - num
    date_under_five = date(today.year,\
                           today.month + remaining, today.day)
    return date_under_five


def delivery_estimate(patient):
    """ Return delivery estimate date
        Params:
            * patient """

    preg_report = PregnancyReport.objects\
        .get(encounter__patient__health_id=patient\
        .encounter.patient.health_id)

    num_month = preg_report.pregnancy_month
    remaining = 9 - num_month

    date_created_on = preg_report.encounter.encounter_date
    year = preg_report.encounter.encounter_date.year
    month_ = preg_report.encounter.encounter_date.month + remaining

    if month_ > 12:
        year = date_created_on.year + 1
        month_ -= 12

    estimate_date = date(year, month_, 1)

    return estimate_date


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


def alerte(nb_date_after):
    """
    Function that calculates the number of days passed between
    the last visit and today's date to see if it happened more
    than 30 days.
    """

    b = False
    ba = False
    icon = ""
    """◉  ◆ ☻ """
    last_visit = nb_date_after
    if nb_date_after >= 8:
        last_visit = nb_date_after
        ba = b = True

    if nb_date_after >= 20:
        last_visit = "! %s !" % nb_date_after
        ba = b = True
        icon ="!"
    return icon, b, ba, last_visit


class Report(PrintedReport):
    title = 'ClientReport'
    filename = 'ClientReport'
    formats = ['html', 'pdf', 'xls']
    argvs = []

    def generate(self, rformat, title, filepath, data):
        doc = Document(title, landscape=True)
        date_today = datetime.today()
        not_first_chw = False

        for chw in CHW.objects.all():

            if not Patient.objects.filter(chw=chw.id,\
                            updated_on__month=date.today().month).count():
                continue

            if chw.clinic:
                section_name = (_("%(clinic)s clinic: %(full_name)s"))\
                   % {'clinic': chw.clinic,\
                      'full_name': chw.full_name()}
            else:
                section_name = chw.full_name()

            # add Page Break before each CHW section.
            if not_first_chw:
                doc.add_element(PageBreak())
                doc.add_element(Section(section_name))
            else:
                doc.add_element(Section(section_name))
                not_first_chw = True

            d_under_five = date_under_five()

            children = Patient.objects.filter(chw=chw.id,\
                                              dob__gt=d_under_five,
                                              updated_on__month=date\
                                              .today().month)\
                              .order_by('last_name', 'first_name')[:5]

            if children:
                table1 = Table(12)
                table1.add_header_row([
                    Text((u'')),
                    Text((u'#')),
                    Text(_(u'Name')),
                    Text(_(u'Gender')),
                    Text(_(u'Age')),
                    Text(_(u"Mother's name")),
                    Text(_(u'Location')),
                    Text(_(u'RDT+')),
                    Text(_(u'MUAC (+/-)')),
                    Text(_(u'Last Visit')),
                    Text(_(u'PID')),
                    Text(_(u'Instructions'))
                    ])

                doc.add_element(Paragraph(_(u'CHILDREN')))

                num = 0

                for child in children:
                    num += 1

                    # rate of change of muac
                    nutrition_report = NutritionReport.objects\
                    .filter(encounter__patient__health_id=child\
                    .health_id).order_by('-encounter__encounter_date')

                    rate_muac = '-'
                    if len(nutrition_report) > 1:
                        rate_muac = ((nutrition_report[0].muac \
                                    - nutrition_report[1].muac) * 100)\
                                    / (nutrition_report[0].muac \
                                    + nutrition_report[1].muac)

                    # RDT test status
                    rdt_result = rdt(child.health_id)

                    # muac
                    try:
                        muac = NutritionReport.objects.\
                            filter(encounter__patient__health_id=child.\
                            health_id)\
                            .order_by('-encounter__encounter_date')[0]\
                            .muac
                    except NutritionReport.DoesNotExist:
                        muac = '-'
                    except IndexError:
                        muac = '-'

                    if child.mother:
                        mother = child.mother.full_name()
                    else:
                        mother = '-'

                    #We pass a parameter the number of days since the
                    #last visit to the alert function.
                    icon, b, ba, last_visit = alerte((date_today\
                                            - child.updated_on).days)

                    #We check if the child has not yet 2 months.
                    child_age = child.humanised_age()\
                                .split(child.humanised_age()[-1])[0]
                    b1 = False
                    if child.humanised_age()[-1] == "w":
                        if int(child_age) < 5:
                            ba = b1 = True
                    if child.humanised_age()[-1] == "m":
                        if int(child_age) < 2:
                            ba = b1 = True

                    table1.add_row([
                        Text(icon),
                        Text(num),
                        Text(child.full_name(), bold=ba),
                        Text(child.gender),
                        Text(child.humanised_age(), bold=b1),
                        Text(mother),
                        Text(child.location.name),
                        Text(rdt_result),
                        Text(('%(muac)s (%(rate_muac)s )' % \
                                            {'rate_muac': rate_muac, \
                                             'muac': muac})),
                        Text(last_visit, bold=b),
                        Text(child.health_id.upper()),
                        Text('')
                        ])

                doc.add_element(table1)

            pregnant_women = \
                   PregnancyReport.objects\
                                .filter(encounter__chw=chw.id,
                                encounter__encounter_date__month=date\
                                .today().month)[:5]

            if pregnant_women:
                table2 = Table(12)
                table2.add_header_row([
                    Text((u'')),
                    Text((u'#')),
                    Text(_(u'Name')),
                    Text(_(u'Age')),
                    Text(_(u'Location')),
                    Text(_(u'Pregnancy')),
                    Text(_(u'# children')),
                    Text(_(u'RDT+')),
                    Text(_(u'Last Visit')),
                    Text(_(u'Next ANC')),
                    Text(_(u'PID')),
                    Text(_(u'Instructions'))
                    ])

                doc.add_element(Paragraph(_(u'PREGNANT WOMEN')))

                num = 0

                for woman in pregnant_women:
                    estimate_date = delivery_estimate(woman)
                    num += 1

                    # RDT test status
                    rdt_result = rdt(woman.pregnancyreport.encounter\
                                          .patient.health_id)

                    #We pass a parameter the number of days since the
                    #last visit to the alert function.
                    icon, b, ba, last_visit = alerte((date_today\
                                - woman.pregnancyreport.encounter\
                                            .patient.updated_on).days)
                    table2.add_row([
                    Text(icon),
                    Text(num),
                    Text(str(woman.pregnancyreport.encounter.\
                                        patient.full_name()), bold=ba),
                    Text(woman.pregnancyreport.encounter\
                                              .patient.humanised_age()),
                    Text(woman.pregnancyreport.encounter\
                                              .patient.location.name),
                    Text('%(month)s m(%(date)s)' %\
                            {'month': woman.pregnancy_month,\
                             'date': estimate_date.strftime("%b %y")}),
                    Text(woman.pregnancyreport.encounter.patient.child \
                                              .all().count()),
                    Text(rdt_result),
                    Text(last_visit, bold=b),
                    Text(''),
                    Text(woman.pregnancyreport.encounter\
                                              .patient.health_id.upper()),
                    Text('')
                    ])

                doc.add_element(table2)

            women = Patient.objects.\
                            filter(chw=chw.id, gender='F',\
                                               dob__lt=d_under_five,
                                               updated_on__month=date\
                                               .today().month)[:5]

            if women:

                table3 = Table(10)
                table3.add_header_row([
                    Text((u'')),
                    Text((u'#')),
                    Text(_(u'Name')),
                    Text(_(u'Age')),
                    Text(_(u'Location')),
                    Text(_(u'# children')),
                    Text(_(u'RDT+')),
                    Text(_(u'Last Visit')),
                    Text(_(u'PID#')),
                    Text(_(u'Instructions'))
                    ])

                doc.add_element(Paragraph(_(u'WOMEN')))

                num = 0

                for woman in women:
                    num += 1

                    # RDT test status

                    rdt_result = rdt(woman.health_id)

                    icon, b, ba, last_visit = alerte((date_today\
                                            - woman.updated_on).days)

                    table3.add_row([
                    Text(icon),
                    Text(num),
                    Text(woman.full_name(),bold=ba),
                    Text(woman.humanised_age()),
                    Text(woman.location.name),
                    Text(woman.child.all().count()),
                    Text(rdt_result),
                    Text(last_visit, bold=b),
                    Text(woman.health_id.upper()),
                    Text('')
                    ])

                doc.add_element(table3)

        return render_doc_to_file(filepath, rformat, doc)
