#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import os
import copy
import csv
import cProfile
from time import time
from datetime import datetime
from types import StringType

from rapidsms.webui.utils import render_to_response

from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.template import Template, Context
from django.http import HttpResponse
from django.db.models import F

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

from childcount.models import Clinic
from childcount.models import CHW
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

def all_patient_list_pdf(request, rfilter=u'all', rformat="html"):
    report_title = ThePatient._meta.verbose_name
    rows = []
    if rfilter == 'underfive':
        reports = ThePatient.under_five()
    else:
        reports = ThePatient.objects.all().order_by('chw', 'household')

    columns, sub_columns = ThePatient.patients_summary_list()

    if rformat == 'pdf':
        for report in reports:
            rows.append([data for data in columns])
        rpt = PDFReport()
        rpt.setTitle(report_title)
        rpt.setFilename('_'.join(report_title.split()))
        rpt.setTableData(reports, columns, _("All Patients"))
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
            return render_to_response(request, 'childcount/patient.html', \
                                        context_dict)
        else:
            return render_to_response(request, 'childcount/patient.html', \
                                        context_dict)


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

    columns, sub_columns = ThePatient.patients_summary_list()

    chws = TheCHWReport.objects.all()
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

def a_surveyreport(request, rformat="html"):
    doc = ccdoc.Document(u'Household Healthy Survey Report')
    today = datetime.today()
    locations = Location.objects.filter(pk__in=CHW.objects.values('location')\
                                                    .distinct('location'))
    headings = TheBHSurveyReport.healthy_survey_columns()
    for location in locations:
        brpts = BedNetReport.objects.filter(encounter__chw__location=location)
        if not brpts.count():
            continue
        t = ccdoc.Table(headings.__len__())
        t.add_header_row([
                    ccdoc.Text(c['name']) for c in headings])
        for row in TheBHSurveyReport.objects.filter(location=location):
            ctx = Context({"object": row})
            row = []
            for cell in headings:
                cellItem = Template(cell['bit']).render(ctx)
                if cellItem.isdigit():
                    cellItem = int(cellItem)
                cellItem = ccdoc.Text(cellItem)
                row.append(cellItem)
            t.add_row(row)
        doc.add_element(ccdoc.Section(u"%s" % location))
        doc.add_element(t)
    return render_doc_to_response(request, rformat, doc, 'hhsurveyrpt')

def household_surveyreport(location=None):
    '''
    Generate the healthy survey report.
    '''
    filename = report_filepath('HouseholdSurveyReport.pdf')
    f = open(filename, 'w')

    story = []

    if TheCHWReport.objects.all().count():
        for chw in TheCHWReport.objects.all():
            if not ThePatient.objects.filter(\
                                health_id=F('household__health_id')).count():
                continue
            tb = household_surveyreportable(chw, ThePatient.objects.filter(\
                    health_id=F('household__health_id'), chw=chw).\
                    order_by('location'))
            story.append(tb)
            story.append(PageBreak())

    doc = SimpleDocTemplate(f, pagesize=landscape(A4), \
                            topMargin=(0 * inch), \
                            bottomMargin=(0 * inch))
    doc.build(story)

    f.close()


def household_surveyreportable(title, indata=None):
    styleH3.fontName = 'Times-Bold'
    styleH3.alignment = TA_CENTER
    styleN2 = copy.copy(styleN)
    styleN2.alignment = TA_CENTER
    styleN3 = copy.copy(styleN)
    styleN3.alignment = TA_RIGHT

    cols, subcol = ThePatient.bednet_summary_minimal()

    hdata = [Paragraph('%s' % title, styleH3)]
    hdata.extend((len(cols) - 1) * [''])
    data = [hdata]

    thirdrow = ['#', RotatedParagraph(Paragraph(cols[0]['name'], styleH3), \
                                1.3 * inch, 0.25 * inch)]
    thirdrow.extend([Paragraph(cols[1]['name'], styleN)])
    thirdrow.extend([Paragraph(cols[2]['name'], styleN)])
    thirdrow.extend([RotatedParagraph(Paragraph(col['name'], styleN), \
                                1.3 * inch, 0.25 * inch) for col in cols[3:]])
    data.append(thirdrow)

    rowHeights = [None, 1.3 * inch]
    colWidths = [0.3 * inch, 0.6 * inch, 0.8 * inch, 1.5 * inch]
    colWidths.extend((len(cols) - 3) * [0.5 * inch])

    if indata:
        c = 0
        for row in indata:
            c = c + 1
            ctx = Context({"object": row})
            values = ["%d" % c, \
                        Paragraph(Template(cols[0]["bit"]).render(ctx), \
                        styleN)]
            values.extend([Paragraph(Template(col["bit"]).render(ctx), \
                                styleN3) for col in cols[1:]])
            data.append(values)
        rowHeights.extend(len(indata) * [0.25 * inch])
    tb = ScaledTable(data, colWidths=colWidths, rowHeights=rowHeights, \
            repeatRows=2)
    tb.setStyle(TableStyle([('SPAN', (0, 0), (colWidths.__len__() - 1, 0)),
                            ('INNERGRID', (0, 0), (-1, -1), 0.1, \
                            colors.lightgrey),\
                            ('BOX', (0, 0), (-1, -1), 0.1, \
                            colors.lightgrey),
                            ('BOX', (4, 1), (8, -1), 5, \
                            colors.lightgrey),
                            ('BOX', (9, 1), (12, -1), 5, \
                            colors.lightgrey),
                            ('BOX', (13, 1), (14, -1), 5, \
                            colors.lightgrey),
                            ('BOX', (15, 1), (16, -1), 5, \
                            colors.lightgrey)]))
    return tb

