import calendar
from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from django.utils import simplejson
from django.http import HttpResponse

from locations.models import Location

from childcount.models import AppointmentReport
from childcount.models import AntenatalVisitReport
from childcount.models import Patient, Clinic

from ccdoc import Document, Table, Paragraph, Text, Section, PageBreak
from childcount.reports.utils import render_doc_to_response

open_status = (AppointmentReport.STATUS_OPEN, \
                    AppointmentReport.STATUS_PENDING_CV)


def defaulters(request, rformat="html"):
    doc = pmtct_defaulters()
    return render_doc_to_response(request, rformat, doc, 'pmtct-defaulters')


def pmtct_defaulters(title=u"Defaulters Report"):
    doc = Document(title, landscape=True, stick_sections=True)
    today = datetime.today() + relativedelta(days=-3)
    for clinic in Clinic.objects.all():
        df = AppointmentReport.objects.filter(status__in=open_status,
                                appointment_date__lt=today,
                                encounter__patient__chw__clinic=clinic,
                            encounter__patient__status=Patient.STATUS_ACTIVE)
        df = df.order_by('encounter__patient__chw',
            'encounter__chw__location',
            'appointment_date')

        t = Table(5)
        t.add_header_row([
            Text(unicode(_(u"Date"))),
            Text(unicode(_(u"Patient"))),
            Text(unicode(_(u"Status"))),
            Text(unicode(_(u"CHW"))),
            Text(unicode(_(u"Location")))])
        for row in df:
            if row.status == AppointmentReport.STATUS_PENDING_CV:
                statustxt = _("Reminded")
            else:
                statustxt = _("Not Reminded")
            t.add_row([
                Text(unicode(row.appointment_date.strftime('%d-%m-%Y'))),
                Text(unicode(row.encounter.patient)),
                Text(unicode(statustxt)),
                Text(unicode(row.encounter.patient.chw)),
                Text(unicode(row.encounter.patient.chw.location))])
        doc.add_element(Section(u"%s" % clinic))
        doc.add_element(t)
        doc.add_element(PageBreak())
    return doc


def appointments(request, rformat="html"):
    doc = Document(unicode(_(u"Appointments Report")))
    today = datetime.today()
    last_30_days = today + relativedelta(days=-30)
    df = AppointmentReport.objects.filter(appointment_date__gte=last_30_days,
                                            appointment_date__lte=today)
    df = df.order_by('encounter__chw__location', 'appointment_date')
    doc.subtitle = unicode(_(u"Appointments Report: Last 30 Days - %(from)s"
                            " to %(to)s" % {"from":
                                        last_30_days.strftime('%d %B, %Y'),
                                        "to": today.strftime('%d %B, %Y')}))
    t = Table(5)
    t.add_header_row([
        Text(unicode(_(u"Date"))),
        Text(unicode(_(u"Reminded?"))),
        Text(unicode(_(u"Patient"))),
        Text(unicode(_(u"CHW"))),
        Text(unicode(_(u"Location")))])
    for row in df:
        if row.status in (AppointmentReport.STATUS_PENDING_CV,
                            AppointmentReport.STATUS_CLOSED):
            statustxt = _("Y")
        else:
            statustxt = _("N")
        t.add_row([
            Text(unicode(row.appointment_date.strftime('%d-%m-%Y'))),
            Text(unicode(statustxt)),
            Text(unicode(row.encounter.patient)),
            Text(unicode(row.encounter.patient.chw)),
            Text(unicode(row.encounter.chw.location))])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, doc, 'pmtct-appointments')


def appointments_error_report(request, rformat="html"):
    doc = Document(unicode(_(u"Error Report")))
    today = datetime.today()
    eigteen_months_ago = today + relativedelta(months=-18)
    twelve_years_ago = today + relativedelta(years=-12)
    df = AppointmentReport.objects.filter()
    df = df.filter(encounter__patient__dob__lt=eigteen_months_ago)
    males = df.filter(encounter__patient__gender=Patient.GENDER_MALE)
    females = df.filter(encounter__patient__gender=Patient.GENDER_FEMALE)
    females = females.filter(encounter__patient__dob__gte=twelve_years_ago)
    males = males.order_by('encounter__chw__location', 'appointment_date')
    females = females.order_by('encounter__chw__location', 'appointment_date')
    t = Table(5)
    t.add_header_row([
        Text(unicode(_(u"Date"))),
        Text(unicode(_(u"Status"))),
        Text(unicode(_(u"Patient"))),
        Text(unicode(_(u"CHW"))),
        Text(unicode(_(u"Location")))])
    for df in [females, males]:
        for row in df:
            if row.status == AppointmentReport.STATUS_PENDING_CV:
                statustxt = _("Open")
            elif row.status == AppointmentReport.STATUS_CLOSED:
                statustxt = _("Closed")
            else:
                statustxt = _("Open")
            t.add_row([
                Text(unicode(row.appointment_date.strftime('%d-%m-%Y'))),
                Text(unicode(statustxt)),
                Text(unicode(row.encounter.patient)),
                Text(unicode(row.encounter.patient.chw)),
                Text(unicode(row.encounter.chw.location))])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, doc,
                                    'pmtct-apts-error')


def appointments_aggregates(request, rformat="html"):
    doc = Document(unicode(_(u"Appointments Aggregates Report ")))
    today = datetime.today()
    last_30_days = today + relativedelta(days=-30)
    df = AppointmentReport.objects.filter(appointment_date__gte=last_30_days,
                                            appointment_date__lte=today)
    # df = df.order_by('encounter__chw__location', 'appointment_date')
    df = df.values('encounter__chw__location__name', 'status')
    df = df.annotate(count=Count('encounter'))
    df = df.order_by('encounter__chw__location__name')
    doc.subtitle = unicode(_(u"Apointments Aggregates Report: Last 30 Days"
                            " - %(from)s to %(to)s" % {"from":
                                        last_30_days.strftime('%d %B, %Y'),
                                        "to": today.strftime('%d %B, %Y')}))
    t = Table(3)
    t.add_header_row([
        Text(unicode(_(u"Location"))),
        Text(unicode(_(u"Reminded?"))),
        Text(unicode(_(u"Count")))])

    count = {AppointmentReport.STATUS_PENDING_CV: 0,
            AppointmentReport.STATUS_CLOSED: 0,
            AppointmentReport.STATUS_OPEN: 0}
    for row in df:
        if row['status'] in (AppointmentReport.STATUS_PENDING_CV,
                            AppointmentReport.STATUS_CLOSED):
            statustxt = _("Y")
        else:
            statustxt = _("N")
        count[row['status']] += row['count']
        t.add_row([
            Text(unicode(row['encounter__chw__location__name'])),
            Text(unicode(statustxt)),
            Text(unicode(row['count']))])

    t.add_row([Text(u""), Text(u""), Text(u"")])
    total_yes = count[AppointmentReport.STATUS_CLOSED] + \
                                count[AppointmentReport.STATUS_PENDING_CV]
    t.add_row([Text(u"Total"), Text(u"Y"),
                Text(unicode(total_yes))])
    t.add_row([Text(u"Total"), Text(u"N"),
                Text(unicode(count[AppointmentReport.STATUS_OPEN]))])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, doc,
                                    'pmtct-apts-aggregate')


def appointments_by_clinic(request, rformat="html"):
    doc = Document(unicode(_(u"Apointments by Clinic")))
    today = datetime.today()
    last_30_days = today + relativedelta(days=-30)
    df = AppointmentReport.objects.filter(appointment_date__gte=last_30_days,
                                            appointment_date__lte=today)
    doc.subtitle = unicode(_(u"Apointments by Clinic Report: Last 30 Days"
                            " - %(from)s to %(to)s" % {"from":
                                        last_30_days.strftime('%d %B, %Y'),
                                        "to": today.strftime('%d %B, %Y')}))
    t = Table(5)
    t.add_header_row([
        Text(unicode(_(u"Location"))),
        Text(unicode(_(u"Total number of appointments made"))),
        Text(unicode(_(u"Number of defaulters"))),
        Text(unicode(_(u"Percentage defaulting (defaulters/total "
                        "appointments)"))),
        Text(unicode(_(u"Percentage reminded (reminders over total # of "
                        "appointments.")))])
    total = 0
    total_defaulters = 0
    total_reminded = 0
    for clinic in Clinic.objects.all():
        apts = df.filter(encounter__chw__clinic=clinic)
        defaulters = apts.exclude(status=AppointmentReport.STATUS_CLOSED)
        reminded = apts.filter(status__in=(AppointmentReport.STATUS_PENDING_CV,
                                AppointmentReport.STATUS_CLOSED))
        total += apts.count()
        total_defaulters += defaulters.count()
        total_reminded += reminded.count()
        if apts.count() == 0:
            percentage_default = u""
            percentage_reminded = u""
        else:
            percentage_default = u"%s%%" % round((defaulters.count() /  \
                                    float(apts.count())) * 100, 2)
            percentage_reminded = u"%s%%" % round((reminded.count() /  \
                                    float(apts.count())) * 100, 2)
        t.add_row([
            Text(unicode(clinic)),
            Text(unicode(apts.count())),
            Text(defaulters.count()),
            Text(percentage_default),
            Text(percentage_reminded)])
    percentage_default = u""
    percentage_reminded = u""
    if total != 0:
        percentage_default = u"%s%%" % round((total_defaulters /  \
                                    float(total)) * 100, 2)
        percentage_reminded = u"%s%%" % round((total_reminded /  \
                                    float(total)) * 100, 2)
    t.add_row([Text(u"Total"),
        Text(unicode(total)),
        Text(unicode(total_defaulters)),
        Text(percentage_default),
        Text(percentage_reminded)])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, doc,
                                    'pmtct-apts-by-clinic')


def upcoming_deliveries(request, rformat="html"):
    doc = Document(unicode(_(u"Upcoming Deliveries")))
    today = datetime.today()
    two_weeks_time = today + relativedelta(weeks=2)
    ud = AntenatalVisitReport.objects.filter(expected_on__gte=today, \
                        expected_on__lte=two_weeks_time, \
                        encounter__patient__status=Patient.STATUS_ACTIVE)
    ud = ud.order_by('encounter__patient__chw__location')

    t = Table(3)
    t.add_header_row([
        Text(unicode(_(u"Patient"))),
        Text(unicode(_(u"CHW"))),
        Text(unicode(_(u"Location")))])
    for row in ud:
        t.add_row([
            Text(unicode(row.encounter.patient)),
            Text(unicode(row.encounter.patient.chw)),
            Text(unicode(row.encounter.patient.chw.location))])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, doc, 'pmtct-deliveries')


def statistics(request, rformat="html"):
    # TODO: html and pdf formats
    mimetype = 'application/javascript'
    data = simplejson.dumps(summary())
    return HttpResponse(data, mimetype)


def summary():
    '''Calculates Total Defaulters and Total Defaulters Per Location'''
    today = datetime.today()
    df = AppointmentReport.objects.filter(status__in=open_status, \
                                            appointment_date__lt=today, \
                            encounter__patient__status=Patient.STATUS_ACTIVE)
    total_defaulters = df.count()
    # summary per clinic
    dfl = AppointmentReport.objects.filter(status__in=open_status, \
                            appointment_date__lt=today, \
                            encounter__patient__status=Patient.STATUS_ACTIVE)
    dfl = dfl.values('encounter__patient__chw__location')
    dfl = dfl.annotate(num_defaulters=Count('encounter'))
    clinics = []
    for c in dfl:
        loc = Location.objects.get(pk=c['encounter__patient__chw__location'])
        clinics.append({'location': loc.name, \
                        'defaulters': c['num_defaulters']})
    data = {'total': total_defaulters, 'clinics': clinics}
    return data


def new_registrations(request, rformat="html"):
    '''Weekly, the number of new mother/infant pairs registered into the
    system - Based solely on First Visit report i.e +PF'''
    # TODO: Need to include under five as well
    doc = Document(unicode(_(u"New Registrations")))
    today = datetime.today()
    start = today + relativedelta(days=-7, weekday=calendar.MONDAY)
    r = AntenatalVisitReport.objects
    r = r.filter(encounter__encounter_date__gte=start, \
                            encounter__patient__status=Patient.STATUS_ACTIVE)
    r = r.order_by('encounter__patient__chw__location')

    t = Table(3)
    t.add_header_row([
        Text(unicode(_(u"Patient"))),
        Text(unicode(_(u"CHW"))),
        Text(unicode(_(u"Location")))])
    for row in r:
        t.add_row([
            Text(unicode(row.encounter.patient)),
            Text(unicode(row.encounter.patient.chw)),
            Text(unicode(row.encounter.patient.chw.location))])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, doc, 'new-registrations')


def active_mothers(request, rformat="html"):
    '''Total number of mothers followed currently, overall and broken down
    by location - dob is atleast 10 yrs ago'''
    # TODO: Need to include under five as well
    doc = Document(unicode(_(u"Mothers Being followed")))
    today = datetime.today()
    ten_years_ago = today + relativedelta(years=-10)
    start = ten_years_ago
    r = AppointmentReport.objects.filter(encounter__patient__dob__lt=start, \
                            encounter__patient__status=Patient.STATUS_ACTIVE, \
                            encounter__patient__gender=Patient.GENDER_FEMALE, \
                            status__in=open_status)
    r = r.values('encounter__patient').distinct()
    r = r.order_by('encounter__patient__chw__location')

    t = Table(3)
    t.add_header_row([
        Text(unicode(_(u"Patient"))),
        Text(unicode(_(u"CHW"))),
        Text(unicode(_(u"Location")))])
    for row in r:
        patient = Patient.objects.get(pk=row['encounter__patient'])
        t.add_row([
            Text(unicode(patient)),
            Text(unicode(patient.chw)),
            Text(unicode(patient.chw.location))])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, doc,
                                    'pmtct-mothers-onfollowup')


def upcoming_appointments(title=_(u'Upcoming Apointments')):
    doc = Document(title)
    today = datetime.today()
    next_45days = today + relativedelta(days=45)
    ud = AppointmentReport\
        .objects\
        .filter(appointment_date__gte=today,
            appointment_date__lte=next_45days,
            status=AppointmentReport.STATUS_OPEN)
    ud = ud.order_by('appointment_date', 'encounter__patient__chw')

    for clinic in Clinic.objects.all():
        t = Table(4)
        t.add_header_row([
            Text(unicode(_(u"Patient"))),
            Text(unicode(_(u"Date of Appointment"))),
            Text(unicode(_(u"CHW"))),
            Text(unicode(_(u"Location")))])
        for row in ud.filter(encounter__patient__chw__clinic=clinic):
            t.add_row([
                Text(unicode(row.encounter.patient)),
                Text(unicode(row.appointment_date.strftime("%d-%m-%Y"))),
                Text(unicode(row.encounter.patient.chw)),
                Text(unicode(row.encounter.patient.chw.location))])
        t.set_alignment(Table.ALIGN_LEFT, column=0)
        t.set_alignment(Table.ALIGN_CENTER, column=1)
        t.set_alignment(Table.ALIGN_LEFT, column=2)
        t.set_alignment(Table.ALIGN_LEFT, column=3)
        t.set_column_width(16, column=3)
        doc.add_element(Section(u"%(clinic)s: Upcoming Appointments "\
            "%(from)s to %(to)s" % {'clinic': clinic,
            'from': today.strftime("%d %b"),
            'to': next_45days.strftime("%d %b")}))
        doc.add_element(t)
        doc.add_element(PageBreak())
    doc.add_element(t)
    return doc
