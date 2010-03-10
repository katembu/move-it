#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

import datetime
import urllib
import urllib2
import random

from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from rapidsms.webui.utils import render_to_response
from django.core.urlresolvers import reverse
from rapidsms.webui import settings


def index(req):
    template_name = 'dataentry/entry.html'
    return render_to_response(req, template_name, {})


def proxy(req, number, message):
    ''' Proxy forwarding requests to dataentry backend. '''

    conf = settings.RAPIDSMS_APPS['dataentry']
    url = "http://%s:%s" % (conf["host"], conf["port"])

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
