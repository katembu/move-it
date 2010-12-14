import calendar
from datetime import datetime
from dateutil.relativedelta import relativedelta

from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from django.utils import simplejson
from django.http import HttpResponse

from locations.models import Location

from ccdoc import Document, Section, Table, Paragraph, Text

from childcount.models import PolioCampaignReport, Patient, CHW
from childcount.reports.utils import render_doc_to_response


def polio_start_end_dates(phase):
    first_day = PolioCampaignReport.objects.filter(phase=phase)\
                                    .values('created_on')\
                                    .order_by('created_on')[0]['created_on']
    last_day = PolioCampaignReport.objects.filter(phase=phase)\
                                    .values('created_on')\
                                    .order_by('-created_on')[0]['created_on']
    return first_day, last_day


def polio_summary(request, rformat="html"):
    doc = Document(unicode(_(u"Polio Campaign Summary Report")))
    for phase in PolioCampaignReport.objects.values('phase')\
        .order_by('phase').distinct():
        first_day, last_day = polio_start_end_dates(phase['phase'])
        dob = first_day + relativedelta(months=-59)
        underfive = Patient.objects.filter(dob__gte=dob, dob__lt=last_day,
                                    status=Patient.STATUS_ACTIVE)
        rpts = PolioCampaignReport.objects.filter(phase=phase['phase'])
        total = rpts.count()
        percentage = round((total / float(underfive.count())) * 100, 2)
        resp = _(u"%(percentage)s%% coverage, Total Reports: %(total)s. " % \
                {'total': total, 'percentage': percentage})
        rpts = rpts.values('chw__location__name', 'chw__location')
        rpts = rpts.annotate(Count('chw'))
        tail = [
                Text(unicode("Total")),
                Text(unicode(total)),
                Text(unicode(underfive.count())),
                Text(unicode("%s%%" % percentage))]
        t = Table(4)
        t.add_header_row([
            Text(unicode(_(u"Sub Location"))),
            Text(unicode(_(u"Number of Polio Vaccination"))),
            Text(unicode(_(u"# Target"))),
            Text(unicode(_(u"Percentage (%)")))])
        for row in rpts:
            uf = underfive.filter(chw__location__pk=row['chw__location'])
            percentage = round((row['chw__count'] / float(uf.count())) * 100,
                                2)
            t.add_row([
                Text(unicode(row['chw__location__name'])),
                Text(unicode(row['chw__count'])),
                Text(unicode(uf.count())),
                Text(unicode("%s%%" % percentage))])
        t.add_row(tail)
        doc.add_element(Section(_(u"Phase %(phase)s" % {'phase':
                                                        phase['phase']})))
        doc.add_element(t)

    return render_doc_to_response(request, rformat, doc, 'polio-summary')


def polio_summary_by_location(request, phase=1, rformat="html"):
    doc = Document(unicode(_(u"Polio Campaign Summary Report")))
    first_day, last_day = polio_start_end_dates(phase)
    dob = first_day + relativedelta(months=-59)
    underfive = Patient.objects.filter(dob__gte=dob, dob__lt=last_day,
                                status=Patient.STATUS_ACTIVE)
    rpts = PolioCampaignReport.objects.filter(patient__dob__gte=dob,
                                                phase=phase)
    locations = Location.objects.filter(type__name="Sub Location")
    for location in locations:
        loc_underfive = underfive.filter(chw__location=location)
        loc_rpts = rpts.filter(chw__location=location,
                        patient__status=Patient.STATUS_ACTIVE)
        total = loc_rpts.count()
        inactive = rpts.filter(chw__location=location)
        inactive = inactive.exclude(patient__status=Patient.STATUS_ACTIVE)
        overage = PolioCampaignReport.objects.filter(patient__dob__lt=dob,
                                            chw__location=location)
        percentage = round((total / float(loc_underfive.count())) * 100, 2)
        resp = _(u"%(percentage)s%% coverage, Total Reports: %(total)s. " % \
                {'total': total, 'percentage': percentage})
        """loc_rpts = loc_rpts.values('chw__first_name',
                                    'chw__last_name',
                                    'chw')
        loc_rpts = loc_rpts.annotate(Count('chw'))"""
        tail = [
                Text(unicode("Total")),
                Text(unicode(total)),
                Text(unicode(inactive.count())),
                Text(unicode(overage.count())),
                Text(unicode(loc_underfive.count())),
                Text(unicode("%s%%" % percentage))]
        t = Table(6)
        t.add_header_row([
            Text(unicode(_(u"Name"))),
            Text(unicode(_(u"# Vaccinated"))),
            Text(unicode(_(u"# INACTIVE"))),
            Text(unicode(_(u"# OVERAGE"))),
            Text(unicode(_(u"# Target"))),
            Text(unicode(_(u"Percentage (%)")))])
        for chw in CHW.objects.filter(location=location).exclude(clinic=None):
            uf = loc_underfive.filter(chw=chw)
            lrpts = loc_rpts.filter(patient__chw=chw)
            linactive = inactive.filter(patient__chw=chw)
            overage = PolioCampaignReport.objects.filter(patient__dob__lt=dob,
                        patient__chw=chw)
            try:
                percentage = round((lrpts.count() / float(uf.count())) * \
                                                                        100, 2)
            except ZeroDivisionError:
                percentage = 0
            t.add_row([
                Text(unicode("%s" % chw.full_name())),
                Text(unicode(lrpts.count())),
                Text(unicode(linactive.count())),
                Text(unicode(overage.count())),
                Text(unicode(uf.count())),
                Text(unicode("%s%%" % percentage))])
        t.add_row(tail)
        doc.add_element(Section("%s" % location))
        doc.add_element(t)

    return render_doc_to_response(request, rformat, doc,
                                    'polio-summary-by-location-%s' % phase)


def polio_chw_summary(request, code, phase=1, rformat="html"):
    doc = Document(unicode(_(u"Polio Campaign Summary Report")))
    first_day, last_day = polio_start_end_dates(phase)
    dob = first_day + relativedelta(months=-59)
    try:
        location = Location.objects.get(code=code)
    except Location.DoesNotExist:
        return HttpResponse(_(u"No Location with code %s" % code))
    t = Table(5)
    t.add_header_row([
        Text(unicode(_(u"Name"))),
        Text(unicode(_(u"Vaccinated"))),
        Text(unicode(_(u"Target"))),
        Text(unicode(_(u"Remaining"))),
        Text(unicode(_(u"% Coverage")))])
    for chw in CHW.objects.filter(location=location):
        ps = PolioCampaignReport.objects.filter(patient__chw=chw, phase=phase)\
            .values('patient')
        underfive = Patient.objects.filter(dob__gte=dob, dob__lt=last_day,
                                chw=chw, status=Patient.STATUS_ACTIVE)
        t.add_row([
            Text(unicode(chw)),
            Text(unicode(ps.count())),
            Text(unicode(underfive.count())),
            Text(unicode(underfive.exclude(pk__in=ps).count())),
            Text(unicode(u"%s%%" % round((ps.count() / \
                                    float(underfive.count())) * 100, 2)))])
    ps = PolioCampaignReport.objects.filter(phase=phase,
                                            patient__chw__location=location)\
                                            .values('patient')
    underfive = Patient.objects.filter(dob__gte=dob, chw__location=location,
                                        status=Patient.STATUS_ACTIVE)
    t.add_row([
        Text(unicode(u"Total")),
        Text(unicode(ps.count())),
        Text(unicode(underfive.count())),
        Text(unicode(underfive.exclude(pk__in=ps).count())),
        Text(unicode(u"%s%%" % round((ps.count() / \
                                    float(underfive.count())) * 100, 2)))])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, doc,
                                'polio-chw-summary-%s-%s' % (code, phase))


def polio_not_covered(request, username, phase=1, rformat="html"):
    doc = Document(unicode(_(u"Polio Campaign Summary Report")))
    first_day, last_day = polio_start_end_dates(phase)
    dob = first_day + relativedelta(months=-59)
    try:
        chw = CHW.objects.get(username=username)
    except CHW.DoesNotExist:
        return HttpResponse(_(u"No CHW with username %s" % username))
    ps = PolioCampaignReport.objects.filter(patient__chw=chw,
                                            phase=phase).values('patient')
    underfive = Patient.objects.filter(dob__gte=dob, dob__lt=last_day, chw=chw,
                                status=Patient.STATUS_ACTIVE)
    underfive = underfive.exclude(pk__in=ps)

    t = Table(3)
    t.add_header_row([
        Text(unicode(_(u"Name"))),
        Text(unicode(_(u"Sub Location"))),
        Text(unicode(_(u"Clinic")))])
    for patient in underfive:
        t.add_row([
            Text(unicode(patient)),
            Text(unicode(patient.chw.location)),
            Text(unicode(patient.chw.clinic))])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, doc,
                                'polio-not-covered-%s-%s' % (username, phase))


def polio_inactive_reports(request, username, phase=1, rformat="html"):
    doc = Document(unicode(_(u"Polio Campaign Inactive Report")))
    try:
        chw = CHW.objects.get(username=username)
    except CHW.DoesNotExist:
        ps = PolioCampaignReport.objects.filter(phase=phase)
    else:
        ps = PolioCampaignReport.objects.filter(patient__chw=chw, phase=phase)
    ps = ps.exclude(patient__status=Patient.STATUS_ACTIVE)
    ps = ps.order_by('patient__chw')
    t = Table(4)
    t.add_header_row([
        Text(unicode(_(u"Name"))),
        Text(unicode(_(u"Sub Location"))),
        Text(unicode(_(u"Clinic"))),
        Text(unicode(_(u"CHW")))])
    for row in ps:
        patient = row.patient
        t.add_row([
            Text(unicode(patient)),
            Text(unicode(patient.chw.location)),
            Text(unicode(patient.chw.clinic)),
            Text(unicode(patient.chw))])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, doc,
                                'polio-inactive-%s-%s' % (username, phase))


def polio_overage_reports(request, username, phase=1, rformat="html"):
    doc = Document(unicode(_(u"Polio Campaign Overage Report")))
    first_day, last_day = polio_start_end_dates(phase)
    dob = last_day + relativedelta(months=-59)
    try:
        chw = CHW.objects.get(username=username)
    except CHW.DoesNotExist:
        ps = PolioCampaignReport.objects.filter(phase=phase)
    else:
        ps = PolioCampaignReport.objects.filter(patient__chw=chw, phase=phase)
    ps = ps.filter(patient__status=Patient.STATUS_ACTIVE, patient__dob__lt=dob)
    ps = ps.order_by('patient__chw')
    t = Table(4)
    t.add_header_row([
        Text(unicode(_(u"Name"))),
        Text(unicode(_(u"Sub Location"))),
        Text(unicode(_(u"Clinic"))),
        Text(unicode(_(u"CHW")))])
    for row in ps:
        patient = row.patient
        t.add_row([
            Text(unicode(patient)),
            Text(unicode(patient.chw.location)),
            Text(unicode(patient.chw.clinic)),
            Text(unicode(patient.chw))])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, doc,
                                'polio-overage-%s-%s' % (username, phase))
