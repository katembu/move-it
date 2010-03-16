#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

''' dataentry backend client

WIP: Do not use as this will be broken very soon '''

import datetime
import urllib
import urllib2
import random

from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from rapidsms.webui.utils import render_to_response
from django.core.urlresolvers import reverse
from rapidsms.webui import settings
from django.contrib.auth.decorators import login_required

from childcount.models import CHW


@login_required
def index(req):
    ''' displays childcount U.I '''
    today = datetime.date.today().strftime("%Y-%m-%d")
    chws = CHW.objects.all()
    return render_to_response(req, 'dataentry/entry.html', \
                              {'chws': chws, 'today': today})


def proxy(req, number, message):
    ''' HTTP tester compatible proxy to dataentry backend

    will probably disapear soon. '''

    conf = settings.RAPIDSMS_APPS['dataentry']
    url = "http://%s:%s" % (conf["host"], conf["port"])

    number = number.encode('utf8')
    message = message.encode('utf8')

    # quirks for httptester
    if message == "json_resp":
        action = 'list'
    else:
        action = None

    values = [('identity', number), ('message', message), ('action', action)]

    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    stream = urllib2.urlopen(req)

    return HttpResponse(stream.read(), mimetype="application/json")


def post_proxy(request):
    ''' HTTP proxy to forward AJAX calls to dataentry backend '''

    if not request.method == 'POST':
        return HttpResponse(u"POST?")

    conf = settings.RAPIDSMS_APPS['dataentry']
    url = "http://%s:%s" % (conf["host"], conf["port"])

    data = request.POST.urlencode()
    req = urllib2.Request(url, data)
    stream = urllib2.urlopen(req)

    return HttpResponse(stream.read(), mimetype="application/json")
