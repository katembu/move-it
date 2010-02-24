#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

import datetime
import urllib2
import random

from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from rapidsms.webui.utils import render_to_response
from django.core.urlresolvers import reverse
from rapidsms.webui import settings


def index(req):
    template_name = 'dataentry/entry.html'
    return render_to_response(req, template_name, {
    })


def proxy(req, number, message):
    # build the url to the http server running
    # in ajax.app.App via conf hackery
    conf = settings.RAPIDSMS_APPS['dataentry']
    url = "http://%s:%s/%s/%s" \
          % (conf["host"], conf["port"], \
          urllib2.quote(number), urllib2.quote(message))

    f = urllib2.urlopen(url)
    return HttpResponse(f.read())
