#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from rapidsms.webui.utils import render_to_response
from django.utils.translation import gettext_lazy as _
from django.template import Template, Context

from childcount.models.ccreports import TheCHWReport
from childcount.models.ccreports import ThePatient

from libreport.pdfreport import PDFReport, p


def all_patient_list_pdf(request):
    report_title = ThePatient._meta.verbose_name
    rows = []

    reports = ThePatient.objects.all().order_by('chw', 'household')
    
    cols, sub_cols = ThePatient.patients_summary_list()

    for report in reports:
        rows.append([data for data in cols])

    rpt = PDFReport()
    rpt.setTitle(report_title )
    rpt.setFilename(report_title + '.pdf')
    rpt.setTableData(reports, cols, _("All Patients"))
    return rpt.render()


def all_patient_list_per_chw_pdf(request):
    report_title = ThePatient._meta.verbose_name

    rpt = PDFReport()
    rpt.setTitle(report_title )
    rpt.setFilename(report_title + '.pdf')

    cols, sub_cols = ThePatient.patients_summary_list()

    chws = CHW.objects.all()
    for chw in chws:
        rows = []
        reports = ThePatient.objects.filter(chw=chw).order_by('household')
        summary = u"Number of Children: %(num)s" % {'num': reports.count()}
        for report in reports:
            rows.append([data for data in cols])

        sub_title = u"%s %s" % (chw, summary)
        #rpt.setElements([p(summary)])
        rpt.setTableData(reports, cols, chw)
        rpt.setPageBreak()

    return rpt.render()

def chw(request):
    '''Community Health Worker page '''
    report_title = TheCHWReport._meta.verbose_name
    rows = []

    reports = TheCHWReport.objects.filter(role__code='chw')
    columns, sub_columns = TheCHWReport.summary()
    i = 0
    for report in reports:
        patients = ThePatient.objects.filter(chw=report)
        num_patients = patients.count()
        num_under_5 = 0
        for person in patients:
            if person.age_in_days_weeks_months()[2] < 60:
                num_under_5 +=1        
        i += 1
        row = {}
        row["cells"] = [{'value': Template(col['bit']).render(Context({'object': report}))} for col in columns]
        
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
    print columns[1:]
    aocolumns_js = aocolumns_js[:-1]

    aggregate = False
    print columns
    print sub_columns
    print len(rows)
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
        return render_to_response(request, 'childcount/chw.html', context_dict)
    else:
        return render_to_response(request, 'childcount/chw.html', context_dict)
