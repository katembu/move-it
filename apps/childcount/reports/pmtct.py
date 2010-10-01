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
    doc = Document(_(u'Defaulters Report'))
    today = datetime.today()
    df = AppointmentReport.objects.filter(status__in=open_status, \
                                            appointment_date__lt=today, \
                            encounter__patient__status=Patient.STATUS_ACTIVE)
    df = df.order_by('encounter__patient__chw__location')

    t = Table(4)
    t.add_header_row([
        Text(_(u'Patient')),
        Text(_(u'Status')),
        Text(_(u'CHW')),
        Text(_(u'Location'))])
    for row in df:
        if row.status == AppointmentReport.STATUS_PENDING_CV:
            statustxt = _("Reminded")
        else:
            statustxt = _("Not Reminded")
        t.add_row([
            Text(row.encounter.patient, \
                castfunc=lambda a:a),
            Text(statustxt),
            Text(row.encounter.patient.chw),
            Text(row.encounter.patient.chw.location)])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, doc, 'defaulters-list')


def upcoming_deliveries(request, rformat="html"):
    doc = Document(_(u'Upcoming Deliveries Report - within 2 weeks'))
    today = datetime.today()
    two_weeks_time = today + relativedelta(weeks=2)
    ud = AntenatalVisitReport.objects.filter(expected_on__gte=today, \
                        expected_on__lte=two_weeks_time, \
                        encounter__patient__status=Patient.STATUS_ACTIVE)
    ud = ud.order_by('encounter__patient__chw__location')

    t = Table(3)
    t.add_header_row([
        Text(_(u'Patient')),
        Text(_(u'CHW')),
        Text(_(u'Location'))])
    for row in ud:
        t.add_row([
            Text(row.encounter.patient, \
                castfunc=lambda a: a),
            Text(row.encounter.patient.chw),
            Text(row.encounter.patient.chw.location)])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, doc, 'upcoming-deliveries')


def statistics(request, rformat="html"):
    # TODO: html and pdf formats
    mimetype = 'application/javascript'
    data = simplejson.dumps(summary())
    return HttpResponse(data, mimetype)


def summary():
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
