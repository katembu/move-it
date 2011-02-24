#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: diarra

import calendar
import time
from datetime import datetime, date
from datetime import timedelta

from django.utils.translation import gettext as _

from ccdoc import Document, Table, Paragraph, Text, Section, PageBreak

from childcount.models import Patient, CHW, Encounter
from childcount.reports.utils import render_doc_to_file
from childcount.reports.report_framework import PrintedReport
from childcount.models.reports import (PregnancyReport, FeverReport,
                                       NutritionReport)


ICON_DIAMOND = u'♦'
ICON_FACE = u'☻'
ICON_DANGER = u'!'
ICON_BLANK = U''


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

    return preg_report.encounter.encounter_date + \
        timedelta((9 - preg_report.pregnancy_month) * 30.475)

def rdt(health_id):
    """ RDT test status
        Params:
            * health_id """

    try:
        rdt = FeverReport.objects.\
            filter(encounter__patient__health_id=health_id,\
                                                rdt_result='P').count()
    except FeverReport.DoesNotExist:
        rdt = u'-'

    return rdt


def encounter_alert(visited_days_ago, b_FullName):
    """ Function that calculates the number of days passed between
        the last visit and today's date to see if it happened more
        than 30 days. """

    b_LastVisit = False
    icon = ICON_BLANK
    instruction_text = u''

    date_before_overdue = u''
    day_in_month = calendar.monthrange(date.today().year,\
                                        date.today().month)[1]

    #Calcul of the date where visit will reach 90 days.
    if visited_days_ago >= 60:
        day_deadline = u''
        month_deadline = u''
        year_deadline = u''

        date_before_overdue = date.today() + timedelta(90 - visited_days_ago)
        b_FullName = b_LastVisit = True
        instruction_text = date_before_overdue.strftime(u'Visit HH by %d %b')

    if visited_days_ago >= 90:
        visited_days_ago = u'! %s !' % 'Overdue'
        b_FullName = b_LastVisit = True
        icon = ICON_DANGER

    return icon, b_LastVisit, b_FullName, visited_days_ago, instruction_text


def preg_WomenEncounterAlert(nbr_DayAfterEncounter, b_FullName):
    """
    Function that calculates the number of days passed between
    the last visit and today's date to see if it happened more
    than 30 days.
    """
    b_LastVisit = False
    icon = ICON_BLANK
    last_visit = nbr_DayAfterEncounter
    instruction_text = u''
    date_before_overdue = u''
    day_in_month = calendar.monthrange(date.today().year,\
                                                date.today().month)[1]

    #Calcul of the date where visit will reach 45 days.
    if nbr_DayAfterEncounter >= 15 and nbr_DayAfterEncounter < 45:
        day_deadline = u''
        month_deadline = u''
        year_deadline = u''
        x = date.today()

        if (x.day + (45 - nbr_DayAfterEncounter)) < day_in_month:
            day_deadline = x.day + (45 - nbr_DayAfterEncounter)
            date_before_overdue = date(x.year, x.month, day_deadline)

        else:
            day_deadline = (x.day + (45 - nbr_DayAfterEncounter))\
                                                            - day_in_month
            month_deadline = x.month + 1
            date_before_overdue = date(x.year, month_deadline, day_deadline)

            if month_deadline > 12:
                year_deadline = x.year + 1
                date_before_overdue = date(year_deadline, month_deadline, \
                                           day_deadline)

        instruction_text = date_before_overdue.strftime(u'Visit HH by %d %b')

    if nbr_DayAfterEncounter >= 45:
        last_visit = u'! %s !' % 'Overdue'
        b_FullName = b_LastVisit = True
        icon = ICON_DANGER

    return icon, b_LastVisit, b_FullName, last_visit, instruction_text


def rdt_alert(nb_times_rdt, b_FullName):
    """ returns the rdt alert """

    b_rdt = False
    rdt_result = nb_times_rdt
    icon = ICON_BLANK
    rdt_instruction = u''
    if nb_times_rdt > 3:
        b_FullName = b_rdt = True
        rdt_result = u'! %s !' % rdt_result
        icon = ICON_DANGER
        rdt_instruction = 'check bednet'

    return icon, rdt_result, b_FullName, b_rdt, rdt_instruction

this_month = datetime.today()
last_month = (this_month.replace(day=1) - timedelta(1))

class Report(PrintedReport):
    title = 'ClientReport'
    filename = 'ClientReport'
    formats = ['html', 'pdf', 'xls']
    argvs = []
    variants = [ \
        (this_month.strftime(' - %b'), '_thismonth', \
            {'date': this_month}),
        (last_month.strftime(' - %b'), '_lastmonth', \
            {'date': last_month}),
    ]

    def generate(self, rformat, title, filepath, data):
        doc = Document(title, landscape=True, stick_sections=True)
        not_first_chw = False

        month = data['date'].month
        year = data['date'].year

        for chw in CHW.objects.all().order_by('location'):
            b_FullName = False
            encounters = Encounter.objects\
                        .filter(encounter_date__month=month,\
                                encounter_date__year=year,\
                                                            chw=chw.id)
            if not encounters.count():
                continue

            # result of filter is list of under 5 or women
            # from the encounters list.
            # we skip the CHW is this result is empty.
            if not filter(lambda x: x.patient.is_under_five() \
                                    or x.patient.gender == \
                                              Patient.GENDER_FEMALE, \
                          list(encounters)):
                continue

            # special content for First Page
            if not not_first_chw:
                doc.add_element(Paragraph(_(u'CHW reports one-per page\
                                                starting next page.')))
                not_first_chw = True

            if chw.clinic:
                section_name = (_('%(clinic)s - %(full_name)s')\
                   % {'clinic': chw.clinic.code[0:2],\
                      'full_name': chw.full_name()})
            else:
                section_name = chw.full_name() + ' ' + \
                                time.strftime(u'Data from %b. 1 to %b. %d %Y')

            doc.add_element(Section(section_name))

            children = [Patient.objects.get(id=e['patient']) for e in\
                        Encounter.objects.filter(chw=chw,\
                        encounter_date__month=month,\
                        encounter_date__year=year,\
                        patient__dob__gt=date(year - 5,\
                        month, 1))\
                        .order_by('patient__last_name',\
                        'patient__first_name').values('patient').distinct()]

            if children:
                table1 = Table(12)
                table1.add_header_row([
                    Text(u''),
                    Text(_(u'#')),
                    Text(_(u'Name')),
                    Text(_(u'Gender')),
                    Text(_(u'Age')),
                    Text(_(u'Mother')),
                    Text(_(u'Loc')),
                    Text(_(u'RDT+')),
                    Text(_(u'MUAC (+/-)')),
                    Text(_(u'Visit')),
                    Text(_(u'PID')),
                    Text(_(u'Instructions'))
                    ])

                table1.set_column_width(1, 0)
                table1.set_column_width(5, 1)
                table1.set_column_width(16, 2)
                table1.set_column_width(5, 3)
                table1.set_column_width(5, 4)
                table1.set_column_width(13, 5)
                table1.set_column_width(3, 6)
                table1.set_column_width(4, 7)
                table1.set_column_width(9, 8)
                table1.set_column_width(7, 9)
                table1.set_column_width(5, 10)

                table1.set_alignment(Table.ALIGN_LEFT, column=2)
                table1.set_alignment(Table.ALIGN_LEFT, column=5)
                table1.set_alignment(Table.ALIGN_LEFT, column=8)
                table1.set_alignment(Table.ALIGN_LEFT, column=11)

                doc.add_element(Paragraph(_(u'CHILDREN')))

                num = 0

                for child in children:
                    status = u''
                    num += 1
                    all_instructions = []

                    #Rate of muac
                    nutrition_report = NutritionReport.objects\
                    .filter(\
                        encounter__patient__health_id=child.health_id, \
                        muac__isnull=False)\
                        .order_by('-encounter__encounter_date')

                    rate_muac = u''

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
                        muac = u''
                    except IndexError:
                        muac = u''

                    #Making an alerte if nutrition report change.
                    two_LastReport = []
                    b_FullName = b_muac = False

                    if child.mother:
                        mother = child.mother.full_name()
                    else:
                        mother = u'-'

                    #We pass in parameter the number of days since the
                    #last visit to the alert function.

                    icon, b_LastVisit, b_FullName, last_visit,\
                        instruction_text = encounter_alert(\
                            (data['date'] - child.updated_on).days,\
                            b_FullName)

                    if instruction_text:
                        all_instructions.append(instruction_text)
                    #We check if the child has not yet 2 months.
                    child_age = child.humanised_age()\
                                .split(child.humanised_age()[-1])[0]

                    b_ChildAge = False
                    if child.humanised_age()[-1] == 'w':
                        if int(child_age) < 5:
                            b_FullName = b_ChildAge = True
                    if child.humanised_age()[-1] == 'm':
                        if int(child_age) < 2:
                            b_ChildAge = True
                            b_FullName = b_ChildAge

                    icon, rdt_result, b_FullName, b_rdt, rdt_instruction =\
                                    rdt_alert(rdt_result, b_FullName)

                    if rdt_instruction:
                        all_instructions.append(rdt_instruction)
                    icon_rate = icon_ = instruction = u''
                    sign = u''

                    texte_muac = u''
                    if rate_muac < 0:
                        icon_rate = ICON_DIAMOND
                        b_FullName = b_muac = True
                        sign = ICON_DANGER

                    try:
                        child_muac = NutritionReport.objects\
                                .filter(encounter__patient__health_id=child.\
                                                        health_id).latest()

                        if child_muac.status != 4:
                            b_muac = b_FullName = True
                            icon_ = ICON_DIAMOND
                            instruction = _(u'Nutrition consult')
                            all_instructions.append(instruction)
                            if child_muac.status == 1:
                                status = child_muac.verbose_state
                                print status
                            elif child_muac.status == 2:
                                status = child_muac.verbose_state
                    except NutritionReport.DoesNotExist:
                        pass

                    #if the muac have a value it take a parentheses
                    #if the muac is null it don't take a parentheses
                    if rate_muac == '':
                        texte_muac = (u'%(status)s %(sign)s %(muac)s\
                                        %(rate_muac)s %(sign)s ' % \
                                            {'rate_muac': rate_muac, \
                                             'muac': muac, 'sign': sign,
                                             'status': status})
                    else:
                        texte_muac = (u'%(status)s %(sign)s %(muac)s \
                                        (%(rate_muac)s) %(sign)s ' % \
                                            {'rate_muac': rate_muac, \
                                             'muac': muac, 'sign': sign,
                                             'status': status})

                    table1.add_row([
                        Text((u'%(icon)s %(icon_rate)s %(icon_)s' % \
                                        {'icon':icon, 'icon_': icon_,\
                                            'icon_rate': icon_rate})),
                        Text(num),
                        Text(child.full_name(), bold=b_FullName),
                        Text(child.gender),
                        Text(child.humanised_age(), bold=b_ChildAge),
                        Text(mother),
                        Text(child.location.code),
                        Text(rdt_result, bold=b_rdt),
                        Text(texte_muac, bold=b_muac),
                        Text(last_visit, bold=b_LastVisit),
                        Text(child.health_id.upper()),
                        Text(u', '.join(all_instructions), bold=True)
                        ])

                doc.add_element(table1)

            pregnant_women = \
                   PregnancyReport.objects.filter(\
                        encounter__chw=chw.id, \
                        encounter__encounter_date__month=month,\
                        encounter__encounter_date__year=year)

            if pregnant_women:
                table2 = Table(12)
                table2.add_header_row([
                    Text(u''),
                    Text(_(u'#')),
                    Text(_(u'Name')),
                    Text(_(u'Age')),
                    Text(_(u'Loc')),
                    Text(_(u'Pregnancy')),
                    Text(_(u'Child')),
                    Text(_(u'RDT+')),
                    Text(_(u'Visit')),
                    Text(_(u'Next ANC')),
                    Text(_(u'PID')),
                    Text(_(u'Instructions'))
                    ])

                table2.set_column_width(1, 0)
                table2.set_column_width(5, 1)
                table2.set_column_width(16, 2)
                table2.set_column_width(5, 3)
                table2.set_column_width(3, 4)
                table2.set_column_width(10, 5)
                table2.set_column_width(3, 6)
                table2.set_column_width(5, 7)
                table2.set_column_width(7, 8)
                table2.set_column_width(5, 10)
                table2.set_column_width(8, 9)
                table2.set_column_width(5, 10)

                table2.set_alignment(Table.ALIGN_LEFT, column=2)
                table2.set_alignment(Table.ALIGN_LEFT, column=11)

                doc.add_element(Paragraph(_(u'PREGNANT WOMEN')))

                num = 0

                for woman in pregnant_women:
                    num += 1
                    all_instructions = []

                    # Next anc visit
                    next_anc = next_anc_date(woman)
                    next_anc_alert = False

                    if not next_anc:
                        next_anc_str = _(u'-')
                    else:
                        next_anc_alert = False
                        if next_anc < data['date']:
                            nbr_days = (data['date'] - next_anc).days

                            if nbr_days > 30:
                                next_anc_alert = True
                        next_anc_str = next_anc.strftime('%d-%b')

                    # Delivery estimate date
                    estimate_date = delivery_estimate(woman)

                    # RDT test status
                    rdt_result = rdt(woman.pregnancyreport.encounter\
                                          .patient.health_id)

                    #We pass a parameter the number of days since the
                    #last visit to the alert function.
                    icon, b_LastVisit, b_FullName, last_visit,\
                                    instruction_text =\
                                    preg_WomenEncounterAlert((data['date']\
                                    - woman.pregnancyreport.encounter\
                                    .patient.updated_on).days, b_FullName)

                    if instruction_text:
                        all_instructions.append(instruction_text)

                    icon, rdt_result, b_FullName, b_rdt, rdt_instruction = \
                                        rdt_alert(rdt_result, b_FullName)
                    if rdt_instruction:
                        all_instructions.append(rdt_instruction)

                    instruction = icon_ = u''
                    if (data['date']- estimate_date).days < 30:
                        icon_ = ICON_FACE
                        instruction = _(u'go over personalized birth plan')
                        all_instructions.append(instruction)

                    table2.add_row([
                    Text(_(u'%(icon)s %(icon_)s' % {'icon': icon,\
                                                    'icon_': icon_})),
                    Text(num),
                    Text(str(woman.pregnancyreport.encounter.\
                                    patient.full_name()), bold=b_FullName),
                    Text(woman.pregnancyreport.encounter\
                                              .patient.humanised_age()),
                    Text(woman.pregnancyreport.encounter\
                                              .patient.location.code),
                    Text('%(month)s m(%(date)s)' %\
                            {'month': woman.pregnancy_month,\
                             'date': estimate_date.strftime('%b %y')}),
                    Text(woman.pregnancyreport.encounter.patient.child \
                                              .all().count()),
                    Text(rdt_result, bold=b_rdt),
                    Text(last_visit, bold=b_LastVisit),
                    Text(next_anc_str, bold=next_anc_alert),
                    Text(woman.pregnancyreport.encounter\
                                              .patient.health_id.upper()),
                    Text(u', '.join(all_instructions), bold=True)
                    ])

                doc.add_element(table2)

            pregnant_women_list = [rep.encounter.patient \
                                    for rep in pregnant_women]

            women = [Patient.objects.get(id=e['patient']) for e in\
                    Encounter.objects.filter(chw=chw,\
                    encounter_date__month=data['date'].month,\
                    encounter_date__year=data['date'].year,\
                    patient__gender=Patient.GENDER_FEMALE,\
                    patient__dob__lt=date(data['date'].year - 5,\
                    data['date'].month, data['date'].day))\
                    .order_by('patient__last_name', 'patient__first_name')\
                    .values('patient').distinct()]

            women = list(set(women) - set(pregnant_women_list))

            if women:
                table3 = Table(10)
                table3.add_header_row([
                    Text(u''),
                    Text(_(u'#')),
                    Text(_(u'Name')),
                    Text(_(u'Age')),
                    Text(_(u'Loc')),
                    Text(_(u'Child')),
                    Text(_(u'RDT+')),
                    Text(_(u'Visit')),
                    Text(_(u'PID')),
                    Text(_(u'Instructions'))
                    ])

                table3.set_column_width(1, 0)
                table3.set_column_width(5, 1)
                table3.set_column_width(16, 2)
                table3.set_column_width(5, 3)
                table3.set_column_width(3, 4)
                table3.set_column_width(3, 5)
                table3.set_column_width(5, 6)
                table3.set_column_width(7, 7)
                table3.set_column_width(5, 8)

                table3.set_alignment(Table.ALIGN_LEFT, column=2)
                table3.set_alignment(Table.ALIGN_LEFT, column=9)

                doc.add_element(Paragraph(_(u'WOMEN')))

                num = 0

                for woman in women:
                    num += 1
                    all_instructions = []

                    # RDT test status

                    rdt_result = rdt(woman.health_id)

                    icon, b_LastVisit, b_FullName, last_visit,\
                                        instruction_text\
                                        = encounter_alert((data['date']\
                                        - woman.updated_on).days, b_FullName)

                    if instruction_text:
                        all_instructions.append(instruction_text)

                    icon, rdt_result, b_FullName, b_rdt, rdt_instruction =\
                                        rdt_alert(rdt_result, b_FullName)
                    if rdt_instruction:
                        all_instructions.append(rdt_instruction)

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
                    Text(u', '.join(all_instructions), bold=True)
                    ])

                doc.add_element(table3)

        return render_doc_to_file(filepath, rformat, doc)
