#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _

from rapidsms.webui.utils import render_to_response

from reportgen.models import Report
from reportgen.models import NightlyReport
from reportgen.models import GeneratedReport

from reportgen.utils import nightly_report_data
from reportgen.utils import ondemand_json_obj

from reportgen.timeperiods import period_type_for

PAGES = (
    {'name': _('Report Generation'), \
        'url': '/reportgen/', 'slug': 'index'},
    {'name': _('Nightly Reports'), \
        'url': '/reportgen/nightly/', 'slug': 'nightly'},
    {'name': _('On-Demand Reports'), \
        'url': '/reportgen/ondemand/', 'slug': 'ondemand'},
)

data = {'pages': PAGES}

@login_required
def index(request):
    data['title'] = _('Report Generation')
    return render_to_response(request, "index.html", data)

@login_required
def nightly(request):
    data['title'] = _('Nightly Reports')
    data['nightly'] = [nightly_report_data(n) for n in NightlyReport.objects.all()]
    return render_to_response(request, "nightly.html", data)

@login_required
def ondemand(request):
    if request.method == "POST":
        args = {}
        print request.POST
        report = Report.objects.get(pk=request.POST['report_pk'])
        d = report.get_definition()


        for v in d.variants:
            if request.POST['variant_index'] == v[1]:
                print "%s %s" % (request.POST['variant_index'], v)
                args['variant'] = v
                break
        if 'variant' not in args and request.POST['variant_index'] != 'X':
            raise ValueError(_("Variant not found"))

        args['nightly'] = None
        args['rformat'] = request.POST['rformat']

        period_type = period_type_for(\
            request.POST['period_type_code'])
        print period_type
        args['time_period'] = period_type\
            .periods()[int(request.POST['period_index'])]

        r = d.apply(kwargs=args)
        print r
        data['msg'] = _('Report generation started!')
        
    data['title'] = _('On-Demand Reports')
    data['gen'] = GeneratedReport.objects.order_by('-started_at')[0:30]
    data['data'] = ondemand_json_obj()
    return render_to_response(request, "ondemand.html", data)

