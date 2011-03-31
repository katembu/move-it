#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga
from django.contrib.auth.decorators import login_required

from rapidsms.webui.utils import render_to_response

from reportgen.models import Report
from reportgen.models import NightlyReport
from reportgen.models import GeneratedReport
from reportgen.timeperiods import PERIOD_TYPES
from reportgen.utils import nightly_report_data

PAGES = (
    {'name': 'Report Generation', \
        'url': '/reportgen/', 'slug': 'index'},
    {'name': 'Nightly Reports', \
        'url': '/reportgen/nightly/', 'slug': 'nightly'},
    {'name': 'On-Demand Reports', \
        'url': '/reportgen/ondemand/', 'slug': 'ondemand'},
)

data = {'pages': PAGES}

@login_required
def index(request):
    data['title'] = 'Report Generation'
    return render_to_response(request, "index.html", data)

@login_required
def nightly(request):
    data['title'] = 'Nightly Reports'
    data['nightly'] = [nightly_report_data(n) for n in NightlyReport.objects.all()]
    return render_to_response(request, "nightly.html", data)

@login_required
def ondemand(request):
    data['title'] = 'On-Demand Reports'
    data['reports'] = Report.objects.order_by('title')
    data['periods'] = PERIOD_TYPES
    data['gen'] = GeneratedReport.objects.order_by('-started_at')[0:30]
    return render_to_response(request, "ondemand.html", data)


