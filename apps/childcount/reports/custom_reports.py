#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import os
import copy
import csv
import cProfile
from time import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, MONTHLY
from types import StringType

from rapidsms.webui.utils import render_to_response

from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.template import Template, Context
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import F
from django.db.models import Count

from cStringIO import StringIO

try:
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import letter, landscape, A4
    from reportlab.platypus import Paragraph, SimpleDocTemplate, PageBreak
    from reportlab.platypus import Table, TableStyle, NextPageTemplate
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
except ImportError:
    pass

from childcount.models import Clinic, CHW, Patient, FormGroup, CCReport
from childcount.models import Encounter
from childcount.models.reports import BedNetReport
from childcount.models.ccreports import TheCHWReport
from childcount.models.ccreports import ThePatient, OperationalReport
from childcount.models.ccreports import OperationalReport
from childcount.models.ccreports import ClinicReport
from childcount.models.ccreports import TheBHSurveyReport
from childcount.utils import RotatedParagraph

from libreport.pdfreport import PDFReport, p
from libreport.csvreport import CSVReport
from libreport.pdfreport import MultiColDocTemplate
from libreport.pdfreport import ScaledTable

import ccdoc
from childcount.reports.utils import render_doc_to_response
from childcount.reports.utils import report_filepath

from locations.models import Location

styles = getSampleStyleSheet()

styleN = styles['Normal']
styleH = styles['Heading1']
styleH3 = styles['Heading3']


def all_patient_list_per_chw_pdf(request):
    report_title = ThePatient._meta.verbose_name

    rpt = PDFReport()
    rpt.setTitle(report_title)
    rpt.setFilename('_'.join(report_title.split()))
    rpt.setRowsPerPage(42)

    columns, sub_columns = ThePatient.patients_summary_list()

    chws = TheCHWReport.objects.all()
    for chw in chws:
        rows = []
        reports = ThePatient.objects.filter(chw=chw).order_by('household')
        summary = u"Number of Children: %(num)s" % {'num': reports.count()}
        for report in reports:
            rows.append([data for data in columns])

        sub_title = u"%s %s" % (chw, summary)
        #rpt.setElements([p(summary)])
        rpt.setTableData(reports, columns, chw, hasCounter=True)
        rpt.setPageBreak()

    return rpt.render()


def under_five(request):
    report_title = ThePatient._meta.verbose_name

    rpt = PDFReport()
    rpt.setTitle(report_title)
    rpt.setFilename('_'.join(report_title.split()))
    rpt.setRowsPerPage(42)

    columns, sub_columns = ThePatient.underfive_summary_list()

    chws = [TheCHWReport.objects.all()[2]]
    for chw in chws:
        rows = []
        reports = ThePatient.under_five(chw)
        summary = u"Number of Children: %(num)s" % {'num': reports.count()}
        for report in reports:
            rows.append([data for data in columns])

        sub_title = u"%s %s" % (chw, summary)
        #rpt.setElements([p(summary)])
        rpt.setTableData(reports, columns, chw, hasCounter=True)
        rpt.setPageBreak()
    return rpt.render()


def gen_underfive_register_pdf(f, clinic, rformat):
    story = []
    filename = "underfive-%s.%s" % (clinic, rformat)
    clinic = Clinic.objects.get(code=clinic)
    chws = TheCHWReport.objects.filter(clinic=clinic)
    if not chws.count():
        story.append(Paragraph(_("No report for %s.") % clinic, styleN))
    for chw in chws:
        plist = ThePatient.under_five(chw).filter(status=Patient.STATUS_ACTIVE)

        tb = under_five_table(_(u"CHW: %(loc)s: %(chw)s") % \
                                {'loc': clinic, 'chw': chw}, plist)
        story.append(tb)
        story.append(PageBreak())
        # 108 is the number of rows per page, should probably put this in a
        # variable
        pcount = plist.count()
        if (((pcount / 108) + 1) % 2) == 1 \
            and not (pcount / 108) * 108 == pcount:
            story.append(PageBreak())
    story.insert(0, PageBreak())
    story.insert(0, PageBreak())
    story.insert(0, NextPageTemplate("laterPages"))
    doc = MultiColDocTemplate(report_filename(filename), 2, pagesize=A4, \
                            topMargin=(0.5 * inch), showBoundary=0)
    doc.build(story)
    return HttpResponseRedirect( \
        '/static/childcount/' + REPORTS_DIR + '/' + filename)


def under_five_table(title, indata=None, boxes=None):
    styleH3.fontName = 'Times-Bold'
    styleH3.alignment = TA_CENTER
    styleH5 = copy.copy(styleH3)
    styleH5.fontSize = 8
    styleN.fontSize = 8
    styleN.spaceAfter = 0
    styleN.spaceBefore = 0
    styleN2 = copy.copy(styleN)
    styleN2.alignment = TA_CENTER
    styleN3 = copy.copy(styleN)
    styleN3.alignment = TA_RIGHT
    styleN4 = copy.copy(styleN2)
    styleN4.fontName = 'Times-Bold'

    cols, sub_columns = ThePatient.underfive_summary_list()

    hdata = [Paragraph('%s' % title, styleH3)]
    hdata.extend((len(cols)) * [''])
    cmd = [Paragraph(u"Generated at %s" % \
                    datetime.now().strftime('%Y-%d-%m %H:%M:%S'), styleN)]
    cmd.extend((len(cols)) * [''])
    data = [hdata, cmd]

    firstrow = [Paragraph(u"#", styleH5)]
    firstrow.extend([Paragraph(col['name'], styleH5) for col in cols])
    data.append(firstrow)

    rowHeights = [None, None, 0.2 * inch]
    colWidths = [0.5 * inch, 0.5 * inch, 2.0 * inch, 1.0 * inch]

    ts = [('SPAN', (0, 0), (len(cols), 0)), ('SPAN', (0, 1), (len(cols), 1)),
                            ('LINEABOVE', (0, 2), (len(cols), 2), 1, \
                            colors.black),
                            ('LINEBELOW', (0, 1), (len(cols), 1), 1, \
                            colors.black),
                            ('LINEBELOW', (0, 2), (len(cols), 2), 1, \
                            colors.lightgrey),\
                            ('BOX', (0, 0), (-1, -1), 0.1, \
                            colors.lightgrey)]
    if indata:
        counter = 0
        for row in indata:
            counter += 1
            ctx = Context({"object": row})
            values = [Paragraph("%s" % counter, styleN2)]
            values.extend([Paragraph(Template(cols[0]["bit"]).render(ctx),
                            styleN4)])
            values.extend([Paragraph(Template(col["bit"]).render(ctx), \
                                styleN) for col in cols[1:]])
            data.append(values)
        rowHeights.extend(len(indata) * [0.2 * inch])
    tb = Table(data, colWidths=colWidths, rowHeights=rowHeights, repeatRows=3)
    tb.setStyle(TableStyle(ts))
    return tb


def chw(request, rformat='html'):
    '''Community Health Worker page '''
    report_title = TheCHWReport._meta.verbose_name
    rows = []

    reports = TheCHWReport.objects.filter(role__code='chw')
    columns, sub_columns = TheCHWReport.summary()
    if rformat.lower() == 'pdf':
        rpt = PDFReport()
        rpt.setTitle(report_title)
        rpt.setFilename('_'.join(report_title.split()))

        for report in reports:
            rows.append([data for data in columns])

        rpt.setTableData(reports, columns, report_title)
        rpt.setPageBreak()

        return rpt.render()
    else:
        i = 0
        for report in reports:
            i += 1
            row = {}
            row["cells"] = [{'value': \
                             Template(col['bit']).render(Context({'object': \
                                                report}))} for col in columns]
            if i == 100:
                row['complete'] = True
                rows.append(row)
                break
            rows.append(row)

        aocolumns_js = "{ \"sType\": \"html\" },"
        for col in columns[1:] + (sub_columns if sub_columns != None else []):
            if not 'colspan' in col:
                aocolumns_js += "{ \"asSorting\": [ \"desc\", \"asc\" ], " \
                                "\"bSearchable\": true },"
        aocolumns_js = aocolumns_js[:-1]

        aggregate = False
        context_dict = {'get_vars': request.META['QUERY_STRING'],
                        'columns': columns, 'sub_columns': sub_columns,
                        'rows': rows, 'report_title': report_title,
                        'aggregate': aggregate, 'aocolumns_js': aocolumns_js}

        if request.method == 'GET' and 'excel' in request.GET:
            '''response = HttpResponse(mimetype="application/vnd.ms-excel")
            filename = "%s %s.xls" % \
                       (report_title, datetime.now().strftime("%d%m%Y"))
            response['Content-Disposition'] = "attachment; " \
                                              "filename=\"%s\"" % filename
            from findug.utils import create_excel
            response.write(create_excel(context_dict))
            return response'''
            return render_to_response(request, 'childcount/chw.html', \
                                        context_dict)
        else:
            return render_to_response(request, 'childcount/chw.html', \
                                            context_dict)
