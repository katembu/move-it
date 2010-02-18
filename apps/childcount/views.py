#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from rapidsms.webui.utils import render_to_response
from django.utils.translation import gettext_lazy as _

from childcount.models import Patient


def index(request):
    '''Index page '''
    template_name = "childcount/index.html"
    title = "ChildCount-2.0"
    return render_to_response(request, template_name, {
            "title": title})

def patient(request):
    '''Patients page '''
    report_title = Patient._meta.verbose_name
    rows = []

    reports = Patient.objects.all()
    i = 0
    for report in reports:
        i += 1
        row = {}
        row["cells"] = []
        row["cells"].append({"value": report.health_id.upper()})
        row["cells"].append({"value": report.first_name})
        row["cells"].append({"value": report.last_name})
        row["cells"].append({"value": report.chw})

        if i == 100:
            row['complete'] = True
            rows.append(row)
            break
        rows.append(row)

    columns, sub_columns = Patient.table_columns()

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
        return render_to_response(request, 'childcount/patient.html', context_dict)
    else:
        return render_to_response(request, 'childcount/patient.html', context_dict)
