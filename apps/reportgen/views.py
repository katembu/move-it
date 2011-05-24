#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
import sys
import traceback
import socket
import simplejson

from datetime import datetime

from celery.task.control import inspect

from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect
from django.http import HttpResponseNotFound
from django.http import HttpResponse

from rapidsms.webui.utils import render_to_response

from reportgen.models import Report
from reportgen.models import NightlyReport
from reportgen.models import GeneratedReport

from reportgen.utils import DISPLAY_REPORTS_MAX
from reportgen.utils import nightly_report_data
from reportgen.utils import ondemand_json_obj

from reportgen.timeperiods import period_type_for

PAGES = (
    {'name': _('Nightly Reports'), \
        'url': '/reportgen/nightly/', 'slug': 'nightly'},
    {'name': _('On-Demand Reports'), \
        'url': '/reportgen/ondemand/', 'slug': 'ondemand'},
)

data = {'pages': PAGES}

@login_required
def index(request):
    return HttpResponseRedirect('/reportgen/nightly/')

@login_required
def nightly(request):
    data['title'] = _('Nightly Reports')
    data['nightly'] = [nightly_report_data(n) for n in NightlyReport.objects.all()]
    return render_to_response(request, "nightly.html", data)

@login_required
def ondemand(request):
    if request.method == "POST":
        return _process_gen(request)
    data['title'] = _('On-Demand Reports')
    data['gen'] = GeneratedReport.objects.order_by('-started_at')[0:DISPLAY_REPORTS_MAX]
    data['data'] = ondemand_json_obj()
    
    data['choices'] = simplejson.dumps(GeneratedReport.TASK_STATE_DICT)

    # Get status of celery workers
    # Data workers is a tuple of (is_rabbitmq_up, n_workers)
    i = inspect()
    try:
        p = i.ping()
    except Exception as e:
        data['workers'] = (False, e)
    else:
        if p and len(p) > 0:
            data['workers'] = (True, len(p))
        else:
            data['workers'] = (True, 0)

    return render_to_response(request, "ondemand.html", data)

def _process_gen(request):
    args = {}
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

    period_type = period_type_for(request.POST['period_type_code'])
    pindex = int(request.POST['period_index'])
    args['time_period'] = period_type.periods()[pindex]

    if args['rformat'] not in d.formats:
        raise ValueError('Invalid report format')

    gr = GeneratedReport()
    gr.filename = ''
    gr.title = d.title
    if 'variant' in args:
        gr.variant_title = args['variant']
    gr.report = report
    gr.fileformat = args['rformat']
    gr.period_title = args['time_period'].title
    gr.task_progress = 0
    gr.task_state = GeneratedReport.TASK_STATE_PENDING
    gr.started_at = datetime.now()
    gr.save()

    args['generated_report'] = gr

    print args
    try:
        r = d.apply_async(kwargs=args)
    except socket.error:
        gr.task_state = GeneratedReport.TASK_STATE_FAILED
        gr.finished_at = datetime.now()
        gr.task_progress = 0
        gr.error_message = ''.join(traceback.format_exception(*sys.exc_info()))
        gr.save()

    gr.task_id = r.task_id
    gr.save()
    
    return HttpResponseRedirect('/reportgen/ondemand/')

def delete(request, pk):
    r = GeneratedReport.objects.get(pk=pk)
    r.delete()
    return HttpResponseRedirect('/reportgen/ondemand/')

def ajax_progress(request):
    stats = GeneratedReport\
        .objects\
        .exclude(task_state=GeneratedReport.TASK_STATE_FAILED)\
        .exclude(task_state=GeneratedReport.TASK_STATE_SUCCEEDED)\
        .order_by('-started_at')\
        .values('pk','task_state','task_progress')[0:DISPLAY_REPORTS_MAX]

    ret = simplejson.dumps(list(stats))

    return HttpResponse(ret, mimetype="application/json")

