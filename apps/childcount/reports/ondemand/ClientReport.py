#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: diarra

import calendar

from datetime import datetime, date
from datetime import timedelta

from django.utils.translation import gettext as _

from ccdoc import Document, Table, Paragraph, Text, Section, PageBreak

from childcount.models import Patient, CHW, Encounter
from childcount.reports.utils import render_doc_to_file
from childcount.reports.report_framework import PrintedReport
from childcount.models.reports import (PregnancyReport, FeverReport,
                                       NutritionReport)


def next_anc_date(patient):
    """ returns the date of next visit anc """

    preg_woman = PregnancyReport.objects\
                        .filter(encounter__patient__health_id=patient\
                        .encounter.patient.health_id).latest()

    if not preg_woman.weeks_since_anc:
        return None

    anc_date = None
    encounter_date = preg_woman.encounter.encounter_date
    if preg_woman.weeks_since_anc == 0:
        anc_date = encounter_date + timedelta(30)
    elif preg_woman.weeks_since_anc >= 6:
        anc_date = datetime.today() 
    else:
        weeks_to_anc = 6 - preg_woman.weeks_since_anc
        days_to_anc = 7 * weeks_to_anc

        anc_date = encounter_date + timedelta(days_to_anc)

    return anc_date


def delivery_estimate(patient):
    """ Return delivery estimate date
        Params:
            * patient """

    preg_report = PregnancyReport.objects\
        .filter(encounter__patient__health_id=patient\
        .encounter.patient.health_id).latest()

    num_month = preg_report.pregnancy_month
    remaining = 9 - num_month

    date_created_on = preg_report.encounter.encounter_date
    year = preg_report.encounter.encounter_date.year
    month_ = preg_report.encounter.encounter_date.month + remaining

    if month_ > 12:
        year = date_created_on.year + 1
        month_ -= 12

    estimate_date = datetime(year, month_, 1)

    return estimate_date


def rdt(health_id):
    """ RDT test status
        Params:
            * health_id """

    try:
        rdt = FeverReport.objects.\
            filter(encounter__patient__health_id=health_id,\
                                                rdt_result='P').count()
    except FeverReport.DoesNotExist:
        rdt = '-'

    return rdt


def encounter_alert(nbr_DayAfterEncounter, b_FullName):
    """ Function that calculates the number of days passed between
        the last visit and today's date to see if it happened more
        than 30 days. """

    b_LastVisit = False
    icon = instruction_text = ""

    last_visit = nbr_DayAfterEncounter

    if nbr_DayAfterEncounter >= 60:
        last_visit = nbr_DayAfterEncounter
        b_FullName = b_LastVisit = True
        exceded_days = nbr_DayAfterEncounter - 60
        instruction_text = ("Visit HH by %s")%(exceded_days)

    if nbr_DayAfterEncounter >= 90:
        last_visit = "! %s !" % nbr_DayAfterEncounter
        b_FullName = b_LastVisit = True
        icon = "!"

    return icon, b_LastVisit, b_FullName, last_visit, instruction_text

def preg_WomenEncounterAlert(nbr_DayAfterEncounter, b_FullName):
    """
    Function that calculates the number of days passed between
    the last visit and today's date to see if it happened more
    than 30 days.
    """
    b_LastVisit = False
    icon = ""

    last_visit = nbr_DayAfterEncounter
    instruction_text = ""
    if nbr_DayAfterEncounter >= 15:
        last_visit = nbr_DayAfterEncounter
        b_FullName = b_LastVisit = True
        exceded_days = nbr_DayAfterEncounter - 15
        instruction_text = ("Visit HH by %s")%(exceded_days)

    if nbr_DayAfterEncounter >= 45:
        last_visit = "! %s !" % nbr_DayAfterEncounter
        b_FullName = b_LastVisit = True
        icon = "!"

    return icon, b_LastVisit, b_FullName, last_visit, instruction_text


def rdt_alert(nb_times_rdt, b_FullName):
    """ returns the rdt alert """

    b_rdt = False
    rdt_result = nb_times_rdt
    icon = rdt_instruction = ''
    if nb_times_rdt > 3:
        b_FullName = b_rdt = True
        rdt_result = "! %s !" % rdt_result
        icon = '!'
        rdt_instruction = "check bednet"

    return icon, rdt_result, b_FullName, b_rdt, rdt_instruction


class Report(PrintedReport):
    title = 'ClientReport'
    filename = 'ClientReport'
    formats = ['html', 'pdf', 'xls']
    argvs = []

    def generate(self, rformat, title, filepath, data):
        doc = Document(title, landscape=True, stick_sections=True)
        date_today = datetime.today()
        not_first_chw = False

        for chw in CHW.objects.all().order_by('location'):
            b_FullName = False

            if not Encounter.objects.filter(encounter_date__month=date_today\
            .month, encounter_date__year=date_today.year, chw=chw.id).count():
                continue

            # special content for First Page
            if not not_first_chw:
                doc.add_element(Paragraph(_(u"CHW reports one-per page\
                                                starting next page.")))
                not_first_chw = True

            if chw.clinic:
                section_name = (_("%(clinic)s clinic: %(full_name)s"))\
                   % {'clinic': chw.clinic,\
                      'full_name': chw.full_name()}
            else:
                section_name = chw.full_name()

            doc.add_element(Section(section_name))

            children = [Patient.objects.get(id=e['patient']) for e in\
                        Encounter.objects.filter(chw=chw,\
                        encounter_date__month=date_today.month,\
                        encounter_date__year=date_today.year,\
                        patient__dob__gt=date(date_today.year - 5,\
                        date_today.month, date_today.day))\
                        .order_by('patient__last_name',\
                        'patient__first_name').values('patient').distinct()]

            if children:
                table1 = Table(12)
                table1.add_header_row([
                    Text(u""),
                    Text(_(u"#")),
                    Text(_(u"Name")),
                    Text(_(u"Gender")),
                    Text(_(u"Age")),
                    Text(_(u"Mother")),
                    Text(_(u"Location")),
                    Text(_(u"RDT+")),
                    Text(_(u"MUAC (+/-)")),
                    Text(_(u"Visit")),
                    Text(_(u"PID")),
                    Text(_(u"Instructions"))
                    ])

                table1.set_column_width(4, 0)
                table1.set_column_width(5, 1)
                table1.set_column_width(16, 2)
                table1.set_column_width(5, 3)
                table1.set_column_width(5, 4)
                table1.set_column_width(13, 5)
                table1.set_column_width(5, 6)
                table1.set_column_width(4, 7)
                table1.set_column_width(8, 8)
                table1.set_column_width(5, 9)
                table1.set_column_width(5, 10)

                table1.set_alignment(Table.ALIGN_LEFT, column=2)
                table1.set_alignment(Table.ALIGN_LEFT, column=5)
                table1.set_alignment(Table.ALIGN_CENTER, column=11)

                doc.add_element(Paragraph(_(u'CHILDREN')))

                num = 0

                for child in children:
                    num += 1

                    #Rate of muac
                    nutrition_report = NutritionReport.objects\
                    .filter(\
                        encounter__patient__health_id=child.health_id, \
                        muac__isnull=False)\
                        .order_by('-encounter__encounter_date')

                    rate_muac = '-'

                    if len(nutrition_report) > 1:
                        rate_muac = ((nutrition_report[0].muac \
                                    - nutrition_report[1].muac) * 100)\
                                    / (nutrition_report[0].muac \
                                    + nutrition_report[1].muac)

                    # RDT test status
                    rdt_result = rdt(child.health_id)

                    # geting the muac
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

                    #Making an alerte if nutrition report change.
                    two_LastReport = []
                    b_FullName = b_muac = False

                    #Check if they are more than two report.
                    try:
                        #Get the last two nutrition reports of the child
                        two_LastReport.append(nutrition_report[0])
                        two_LastReport.append(nutrition_report[1])
                        #Checking for a difference between two reports.
                        if two_LastReport[0].muac != two_LastReport[1].muac:
                            b_FullName = b_muac = True
                    except:
                        pass

                    if child.mother:
                        mother = child.mother.full_name()
                    else:
                        mother = '-'

                    #We pass in parameter the number of days since the
                    #last visit to the alert function.

                    icon, b_LastVisit, b_FullName, last_visit, instruction_text =\
                                        encounter_alert((date_today\
                                       - child.updated_on).days, b_FullName)

                    #We check if the child has not yet 2 months.
                    child_age = child.humanised_age()\
                                .split(child.humanised_age()[-1])[0]

                    b_ChildAge = False
                    if child.humanised_age()[-1] == "w":
                        if int(child_age) < 5:
                            b_FullName = b_ChildAge = True
                    if child.humanised_age()[-1] == "m":
                        if int(child_age) < 2:
                            b_ChildAge = True
                            b_FullName = b_ChildAge

                    icon, rdt_result, b_FullName, b_rdt, rdt_instruction = rdt_alert(rdt_result,\
                                                                b_FullName)

                    icon_rate = icon_ = instruction = ''

                    if rate_muac < 0:
                        rate_muac = ('%(muac)s (%(rate_muac)s)' % \
                                            {'rate_muac': rate_muac, \
                                             'muac': muac})
                        icon_rate = u"◆"
                    else:
                        rate_muac = ('%(muac)s (%(rate_muac)s)' % \
                                            {'rate_muac': rate_muac, \
                                             'muac': muac})
                                             
                    try:
                        child_muac = NutritionReport.objects\
                                .filter(encounter__patient__health_id=child.\
                                                        health_id).latest()


                        if child_muac.status != 4:
                            b_FullName = True
                            icon_ = u'◆'
                            instruction = _(u'Nutrition consult')
                    except NutritionReport.DoesNotExist:
                        pass

                    table1.add_row([
                        Text((u"%(icon)s %(icon_rate)s %(icon_)s" % \
                            {'icon':icon, 'icon_': icon_, 'icon_rate': icon_rate})),
                        Text(num),
                        Text(child.full_name(), bold=b_FullName),
                        Text(child.gender),
                        Text(child.humanised_age(), bold=b_ChildAge),
                        Text(mother),
                        Text(child.location.code),
                        Text(rdt_result, bold=b_rdt),
                        Text(rate_muac, bold=b_muac),
                        Text(last_visit, bold=b_LastVisit),
                        Text(child.health_id.upper()),
                        Text(_(u"%(instruction_text)s %(rdt_instruction)s %(instruction)s" %\
                            {'instruction_text': instruction_text,
                             'instruction': instruction,
                             'rdt_instruction': rdt_instruction}), bold=True)
                        ])

                doc.add_element(table1)

            pregnant_women = \
                   PregnancyReport.objects.filter(\
                        encounter__chw=chw.id, \
                        encounter__encounter_date__month=date_today.month, \
                        encounter__encounter_date__year=date_today.year)

            if pregnant_women:
                table2 = Table(12)
                table2.add_header_row([
                    Text(u""),
                    Text(_(u"#")),
                    Text(_(u"Name")),
                    Text(_(u"Age")),
                    Text(_(u"Location")),
                    Text(_(u"Pregnancy")),
                    Text(_(u"Children")),
                    Text(_(u"RDT+")),
                    Text(_(u"Visit")),
                    Text(_(u"Next ANC")),
                    Text(_(u"PID")),
                    Text(_(u"Instructions"))
                    ])

                table2.set_column_width(2, 0)
                table2.set_column_width(5, 1)
                table2.set_column_width(16, 2)
                table2.set_column_width(5, 3)
                table2.set_column_width(5, 4)
                table2.set_column_width(10, 5)
                table2.set_column_width(5, 6)
                table2.set_column_width(5, 7)
                table2.set_column_width(5, 8)
                table2.set_column_width(10, 9)
                table2.set_column_width(5, 10)

                table2.set_alignment(Table.ALIGN_LEFT, column=2)
                table2.set_alignment(Table.ALIGN_CENTER, column=11)

                doc.add_element(Paragraph(_(u'PREGNANT WOMEN')))

                num = 0

                for woman in pregnant_women:
                    num += 1

                    # Next anc visit
                    next_anc = next_anc_date(woman)
                    next_anc_alert = False

                    if not next_anc:
                        next_anc_str = _(u"-")
                    else:
                        next_anc_alert = False
                        if next_anc < date_today:
                            nbr_days = (date_today - next_anc).days

                            if nbr_days > 30:
                                next_anc_alert = True
                        next_anc_str = next_anc.strftime("%d-%b")

                    # Delivery estimate date
                    estimate_date = delivery_estimate(woman)

                    # RDT test status
                    rdt_result = rdt(woman.pregnancyreport.encounter\
                                          .patient.health_id)

                    #We pass a parameter the number of days since the
                    #last visit to the alert function.
                    icon, b_LastVisit, b_FullName, last_visit, instruction_text =\
                                        preg_WomenEncounterAlert((date_today\
                                        - woman.pregnancyreport.encounter\
                                        .patient.updated_on).days, b_FullName)

                    icon, rdt_result, b_FullName, b_rdt, rdt_instruction = rdt_alert(rdt_result,\
                                                                b_FullName)

                    instruction = icon_ = ''
                    if (date_today - estimate_date).days < 21:
                        icon_ = u'☻'
                        instruction = _(u'go over personalized birth plan')

                    table2.add_row([
                    Text(_(u'%(icon)s %(icon_)s' % {'icon': icon, 'icon_': icon_})),
                    Text(num),
                    Text(str(woman.pregnancyreport.encounter.\
                                    patient.full_name()), bold=b_FullName),
                    Text(woman.pregnancyreport.encounter\
                                              .patient.humanised_age()),
                    Text(woman.pregnancyreport.encounter\
                                              .patient.location.code),
                    Text('%(month)s m(%(date)s)' %\
                            {'month': woman.pregnancy_month,\
                             'date': estimate_date.strftime("%b %y")}),
                    Text(woman.pregnancyreport.encounter.patient.child \
                                              .all().count()),
                    Text(rdt_result, bold=b_rdt),
                    Text(last_visit, bold=b_LastVisit),
                    Text(next_anc_str, bold=next_anc_alert),
                    Text(woman.pregnancyreport.encounter\
                                              .patient.health_id.upper()),
                    Text(_(u"%(instruction_text)s %(rdt_instruction)s %(instruction)s" %\
                            {'instruction_text': instruction_text,
                             'instruction': instruction,
                             'rdt_instruction': rdt_instruction}), bold=True)
                    ])

                doc.add_element(table2)
            pregnant_women_list = [rep.encounter.patient \
                                    for rep in pregnant_women]
            women = [Patient.objects.get(id=e['patient']) for e in\
                    Encounter.objects.filter(chw=chw,\
                    encounter_date__month=date_today.month,\
                    encounter_date__year=date_today.year,\
                    patient__gender=Patient.GENDER_FEMALE,\
                    patient__dob__lt=date(date_today.year - 5,\
                    date_today.month, date_today.day))\
                    .order_by('patient__last_name', 'patient__first_name')\
                    .values('patient').distinct()]
            women = list(set(pregnant_women_list) - set(women))

            if women:
                table3 = Table(10)
                table3.add_header_row([
                    Text(u""),
                    Text(_(u"#")),
                    Text(_(u"Name")),
                    Text(_(u"Age")),
                    Text(_(u"Location")),
                    Text(_(u"Children")),
                    Text(_(u"RDT+")),
                    Text(_(u"Visit")),
                    Text(_(u"PID")),
                    Text(_(u"Instructions"))
                    ])

                table3.set_column_width(2, 0)
                table3.set_column_width(5, 1)
                table3.set_column_width(16, 2)
                table3.set_column_width(5, 3)
                table3.set_column_width(5, 4)
                table3.set_column_width(5, 5)
                table3.set_column_width(5, 6)
                table3.set_column_width(5, 7)
                table3.set_column_width(5, 8)

                table3.set_alignment(Table.ALIGN_LEFT, column=2)
                table3.set_alignment(Table.ALIGN_CENTER, column=9)

                doc.add_element(Paragraph(_(u'WOMEN')))

                num = 0

                for woman in women:
                    num += 1

                    # RDT test status

                    rdt_result = rdt(woman.health_id)

                    icon, b_LastVisit, b_FullName, last_visit, instruction_text\
                                        = encounter_alert((date_today\
                                        - woman.updated_on).days, b_FullName)

                    icon, rdt_result, b_FullName, b_rdt, rdt_instruction = rdt_alert(rdt_result,\
                                                              b_FullName)

                    table3.add_row([
                    Text(icon),
                    Text(num),
                    Text(woman.full_name(), bold=b_LastVisit),
                    Text(woman.humanised_age()),
                    Text(woman.location.code),
                    Text(woman.child.all().count()),
                    Text(rdt_result, bold=b_rdt),
                    Text(last_visit, bold=b_LastVisit),
                    Text(woman.health_id.upper()),
                    Text(_(u"%(instruction_text)s %(rdt_instruction)s " %\
                            {'instruction_text': instruction_text,
                            'rdt_instruction': rdt_instruction}), bold=True)
                    ])

                doc.add_element(table3)

        return render_doc_to_file(filepath, rformat, doc)
