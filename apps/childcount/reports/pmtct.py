from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.utils.translation import gettext_lazy as _

from childcount.models import AppointmentReport
from childcount.models import AntenatalVisitReport
from childcount.models import Patient

from ccdoc import Document, Table, Paragraph, Text
from childcount.reports.utils import render_doc_to_response


def defaulters(request, rformat="html"):
    doc = Document(u'Defaulters Report')
    today = datetime.today()
    open_status = (AppointmentReport.STATUS_OPEN, \
                    AppointmentReport.STATUS_PENDING_CV)
    df = AppointmentReport.objects.filter(status__in=open_status, \
                                            appointment_date__lt=today)
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
            Text(row.encounter.patient, 
                castfunc = lambda a: a),
            Text(statustxt),
            Text(row.encounter.patient.chw),
            Text(row.encounter.patient.chw.location)])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, 
        doc, 'defaulters-list')



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
            Text(row.encounter.patient, 
                castfunc = lambda a: a),
            Text(row.encounter.patient.chw),
            Text(row.encounter.patient.chw.location)])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, 
        doc, 'upcoming-deliveries')
