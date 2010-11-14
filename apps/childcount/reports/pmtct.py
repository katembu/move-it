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
from childcount.models import Patient

from ccdoc import Document, Table, Paragraph, Text
from childcount.reports.utils import render_doc_to_response

open_status = (AppointmentReport.STATUS_OPEN, \
                    AppointmentReport.STATUS_PENDING_CV)


def defaulters(request, rformat="html"):
    doc = Document(unicode(_(u'Defaulters Report')))
    today = datetime.today()
    df = AppointmentReport.objects.filter(status__in=open_status, \
                                            appointment_date__lt=today, \
                            encounter__patient__status=Patient.STATUS_ACTIVE)
    df = df.order_by('encounter__patient__chw__location')

    t = Table(4)
    t.add_header_row([
        Text(unicode(_(u'Patient'))),
        Text(unicode(_(u'Status'))),
        Text(unicode(_(u'CHW'))),
        Text(unicode(_(u'Location')))])
    for row in df:
        if row.status == AppointmentReport.STATUS_PENDING_CV:
            statustxt = _("Reminded")
        else:
            statustxt = _("Not Reminded")
        t.add_row([
            Text(unicode(row.encounter.patient)),
            Text(unicode(statustxt)),
            Text(unicode(row.encounter.patient.chw)),
            Text(unicode(row.encounter.patient.chw.location))])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, doc, 'defaulters-list')


def appointments(request, rformat="html"):
    doc = Document(unicode(_(u'Appointments Report')))
    today = datetime.today()
    last_30_days = today + relativedelta(days=-30)
    df = AppointmentReport.objects.filter(appointment_date__gte=last_30_days)
    df = df.order_by('encounter__chw__location', 'appointment_date')
    print df.count()
    t = Table(5)
    t.add_header_row([
        Text(unicode(_(u'Date'))),
        Text(unicode(_(u'Reminded?'))),
        Text(unicode(_(u'Patient'))),
        Text(unicode(_(u'CHW'))),
        Text(unicode(_(u'Location')))])
    for row in df:
        if row.status == AppointmentReport.STATUS_PENDING_CV:
            statustxt = _("Y")
        elif row.status == AppointmentReport.STATUS_CLOSED:
            statustxt = _("NC")
        else:
            statustxt = _("N")
        t.add_row([
            Text(unicode(row.appointment_date.strftime('%d-%m-%Y'))),
            Text(unicode(statustxt)),
            Text(unicode(row.encounter.patient)),
            Text(unicode(row.encounter.patient.chw)),
            Text(unicode(row.encounter.chw.location))])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, doc, 'appointment-list')


def appointments_aggregates(request, rformat="html"):
    doc = Document(unicode(_(u'Appointments Aggregates Report')))
    today = datetime.today()
    last_30_days = today + relativedelta(days=-30)
    df = AppointmentReport.objects.filter(appointment_date__gte=last_30_days)
    # df = df.order_by('encounter__chw__location', 'appointment_date')
    df = df.values('encounter__chw__location__name', 'status')
    df = df.annotate(count=Count('encounter'))

    t = Table(3)
    t.add_header_row([
        Text(unicode(_(u'Location'))),
        Text(unicode(_(u'Reminded?'))),
        Text(unicode(_(u'Count')))])

    count = {AppointmentReport.STATUS_PENDING_CV: 0,
            AppointmentReport.STATUS_CLOSED: 0,
            AppointmentReport.STATUS_OPEN: 0}    
    for row in df:
        if row['status'] == AppointmentReport.STATUS_PENDING_CV:
            statustxt = _("Y")
        elif row['status'] == AppointmentReport.STATUS_CLOSED:
            statustxt = _("NC")
        else:
            statustxt = _("N")
        count[row['status']] += row['count']
        t.add_row([
            Text(unicode(row['encounter__chw__location__name'])),
            Text(unicode(statustxt)),
            Text(unicode(row['count']))])

    t.add_row([Text(u""), Text(u""), Text(u"")])
    t.add_row([Text(u"Total"), Text(u"Y"),
                Text(unicode(count[AppointmentReport.STATUS_PENDING_CV]))])
    t.add_row([Text(u"Total"), Text(u"N"),
                Text(unicode(count[AppointmentReport.STATUS_OPEN]))])
    t.add_row([Text(u"Total"), Text(u"NC"),
                Text(unicode(count[AppointmentReport.STATUS_CLOSED]))])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, doc, 'appointment-aggregate')


def upcoming_deliveries(request, rformat="html"):
    doc = Document(unicode(_(u'Upcoming Deliveries')))
    today = datetime.today()
    two_weeks_time = today + relativedelta(weeks=2)
    ud = AntenatalVisitReport.objects.filter(expected_on__gte=today, \
                        expected_on__lte=two_weeks_time, \
                        encounter__patient__status=Patient.STATUS_ACTIVE)
    ud = ud.order_by('encounter__patient__chw__location')

    t = Table(3)
    t.add_header_row([
        Text(unicode(_(u'Patient'))),
        Text(unicode(_(u'CHW'))),
        Text(unicode(_(u'Location')))])
    for row in ud:
        t.add_row([
            Text(unicode(row.encounter.patient)),
            Text(unicode(row.encounter.patient.chw)),
            Text(unicode(row.encounter.patient.chw.location))])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, doc, 'upcoming-deliveries')


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
    doc = Document(unicode(_(u'New Registrations')))
    today = datetime.today()
    start = today + relativedelta(days=-7, weekday=calendar.MONDAY)
    r = AntenatalVisitReport.objects
    r = r.filter(encounter__encounter_date__gte=start, \
                            encounter__patient__status=Patient.STATUS_ACTIVE)
    r = r.order_by('encounter__patient__chw__location')

    t = Table(3)
    t.add_header_row([
        Text(unicode(_(u'Patient'))),
        Text(unicode(_(u'CHW'))),
        Text(unicode(_(u'Location')))])
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
    doc = Document(unicode(_(u'Mothers Being followed')))
    today = datetime.today()
    ten_years_ago = today + relativedelta(years=-10)
    start = today + relativedelta(days=-7, weekday=calendar.MONDAY)
    r = AppointmentReport.objects.filter(encounter__patient__dob__lt=start, \
                            encounter__patient__status=Patient.STATUS_ACTIVE, \
                            encounter__patient__gender=Patient.GENDER_FEMALE, \
                            status__in=open_status)
    r = r.values('encounter__patient').distinct()
    r = r.order_by('encounter__patient__chw__location')

    t = Table(3)
    t.add_header_row([
        Text(unicode(_(u'Patient'))),
        Text(unicode(_(u'CHW'))),
        Text(unicode(_(u'Location')))])
    for row in r:
        patient = Patient.objects.get(pk=row['encounter__patient'])
        t.add_row([
            Text(unicode(patient)),
            Text(unicode(patient.chw)),
            Text(unicode(patient.chw.location))])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, doc, 'mothers-on-followup')
