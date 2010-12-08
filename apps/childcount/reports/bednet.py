import calendar
from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from django.utils import simplejson
from django.http import HttpResponse

from locations.models import Location

from childcount.models import BednetIssuedReport
from childcount.models import Patient, Clinic

from ccdoc import Document, Table, Paragraph, Text, Section
from childcount.reports.utils import render_doc_to_response


def issued_report(request, rformat="html"):
    doc = Document(unicode(_(u"Defaulters Report")))
    today = datetime.today() + relativedelta(days=-3)
    for clinic in Clinic.objects.all():
        rpts = BednetIssuedReport.objects\
                            .filter(encounter__patient__chw__clinic=clinic)\
                            .order_by('encounter__chw__location')
        t = Table(5)
        t.add_header_row([
            Text(unicode(_(u"Date"))),
            Text(unicode(_(u"Patient"))),
            Text(unicode(_(u"# of Bednets Issued"))),
            Text(unicode(_(u"CHW"))),
            Text(unicode(_(u"Location")))])
        for row in rpts:
            enc_date = row.encounter.encounter_date.strftime('%d-%m-%Y')
            t.add_row([
                Text(unicode(enc_date)),
                Text(unicode(row.encounter.patient)),
                Text(unicode(row.bednet_received)),
                Text(unicode(row.encounter.patient.chw)),
                Text(unicode(row.encounter.patient.chw.location))])
        doc.add_element(Section(u"%s" % clinic))
        doc.add_element(t)
    return render_doc_to_response(request, rformat, doc, 'bednet-issued')
