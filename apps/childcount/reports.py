#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from rapidsms.webui.utils import render_to_response
from django.utils.translation import gettext_lazy as _
from django.template import Template, Context

from childcount.models import Patient
from childcount.models.ccreports import ThePatient

from libreport.pdfreport import PDFReport


def all_patient_list_pdf(request):
    report_title = Patient._meta.verbose_name
    rows = []

    reports = ThePatient.objects.all().order_by('chw', 'household')
    
    cols, sub_cols = ThePatient.patients_summary_list()

    for report in reports:
        rows.append([data for data in cols])
        pass

    rpt = PDFReport()
    rpt.setTitle(report_title )
    rpt.setFilename(report_title + '.pdf')
    rpt.setTableData(reports, cols, _("All Patients"))
    return rpt.render()
