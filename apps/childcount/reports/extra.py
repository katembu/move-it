#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from dateutil.rrule import rrule, MONTHLY

from django.utils.translation import gettext_lazy as _

from ccdoc import Document, Section, Table, Paragraph, Text

from childcount.models import NutritionReport, FeverReport, BedNetReport, CHW
from childcount.reports.utils import render_doc_to_response


def malaria(request, rformat="html"):
    dtstart = FeverReport.objects.filter()\
                                .order_by('encounter__encounter_date')[0]\
                                .encounter.encounter_date
    dtend = FeverReport.objects.filter()\
                                .order_by('-encounter__encounter_date')[0]\
                                .encounter.encounter_date
    doc = Document(unicode(_(u"Malaria reports since %s" % \
                                dtstart.strftime("%B %Y"))))
    t = Table(5)
    t.add_header_row([
            Text(unicode("Month")),
            Text(unicode("Year")),
            Text(unicode("Number of RDT Reports")),
            Text(unicode("Positive Result")),
            Text(unicode("Negative Result"))])
    tt = tp = tn = 0
    for dt in rrule(MONTHLY, bymonthday=1, dtstart=dtstart, until=dtend):
        rpts = FeverReport.objects\
                            .filter(encounter__encounter_date__month=dt.month)
        rpts = rpts.filter(encounter__encounter_date__year=dt.year)
        at = rpts.count()
        p = rpts.filter(rdt_result=FeverReport.RDT_POSITIVE).count()
        n = rpts.filter(rdt_result=FeverReport.RDT_NEGATIVE).count()
        tt += at
        tp += p
        tn += n
        t.add_row([
            Text(unicode(dt.strftime("%B"))),
            Text(unicode(dt.year)),
            Text(unicode(at)),
            Text(unicode(p)),
            Text(unicode(n))])
    t.add_row([
            Text(unicode("")),
            Text(unicode("TOTAL")),
            Text(unicode(tt)),
            Text(unicode(tp)),
            Text(unicode(tn))])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, doc, 'malaria')


def muac(request, rformat="html"):
    dtstart = NutritionReport.objects.filter()\
                                    .order_by('encounter__encounter_date')[0]\
                                    .encounter.encounter_date
    dtend = NutritionReport.objects.filter().\
                                    order_by('-encounter__encounter_date')[0]\
                                    .encounter.encounter_date
    doc = Document(unicode(_(u"Nutrition reports")))
    t = Table(7)
    t.add_header_row([
            Text(unicode("Month")),
            Text(unicode("Year")),
            Text(unicode("Number of Nutrition Reports")),
            Text(unicode("SAM+")),
            Text(unicode("SAM")),
            Text(unicode("MAM")),
            Text(unicode("HEALTHY"))])
    tt = tss = ts = tm = th = 0
    for dt in rrule(MONTHLY, bymonthday=1, dtstart=dtstart, until=dtend):
        rpts = NutritionReport.objects\
                            .filter(encounter__encounter_date__month=dt.month)
        rpts = rpts.filter(encounter__encounter_date__year=dt.year)
        at = rpts.count()
        ss = rpts.filter(status=NutritionReport.STATUS_SEVERE_COMP).count()
        s = rpts.filter(status=NutritionReport.STATUS_SEVERE).count()
        m = rpts.filter(status=NutritionReport.STATUS_MODERATE).count()
        h = rpts.filter(status=NutritionReport.STATUS_HEALTHY).count()
        tt += at
        tss += ss
        ts += s
        tm += m
        th += h
        t.add_row([
            Text(unicode(dt.strftime("%B"))),
            Text(unicode(dt.year)),
            Text(unicode(at)),
            Text(unicode(ss)),
            Text(unicode(s)),
            Text(unicode(m)),
            Text(unicode(h))])
    t.add_row([
            Text(unicode("")),
            Text(unicode("TOTAL")),
            Text(unicode(tt)),
            Text(unicode(tss)),
            Text(unicode(ts)),
            Text(unicode(tm)),
            Text(unicode(th))])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, doc, 'muac')


def samplebednetreports(request, rformat="html"):
    chws = CHW.objects.filter(location__code=u"sauri")
    rpts = BedNetReport.objects.filter(encounter__chw__in=chws).order_by('?')
    sample = rpts[:200]
    doc = Document(unicode(_(u"Bednet Sample")))
    t = Table(9)
    t.add_header_row([
            Text(unicode("#")),
            Text(unicode("HHID")),
            Text(unicode("Name")),
            Text(unicode("# Sleeping Sites")),
            Text(unicode("# Functioning Nets")),
            Text(unicode("# Earlier Nets")),
            Text(unicode("# Damaged Nets")),
            Text(unicode("# Required Nets")),
            Text(unicode("# CHW"))])
    data = {}
    for row in sample:
        if not data.has_key(row.encounter.chw):
            data[row.encounter.chw] = []
        data[row.encounter.chw].append(row)
    counter = 0
    for chw in data:
        for row in data[chw]:
            counter += 1
            required_nets = row.sleeping_sites - row.function_nets
            t.add_row([
                Text(unicode(counter)),
                Text(row.encounter.patient.health_id.upper()),
                Text(row.encounter.patient.full_name()),
                Text(unicode(row.sleeping_sites)),
                Text(unicode(row.function_nets)),
                Text(unicode(row.earlier_nets)),
                Text(unicode(row.damaged_nets)),
                Text(unicode(required_nets)),
                Text(unicode(chw))])
    doc.add_element(t)

    return render_doc_to_response(request, rformat, doc, 'sample')
