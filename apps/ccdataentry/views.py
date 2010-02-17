#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from rapidsms.webui.utils import render_to_response
from django.utils.translation import gettext_lazy as _
from django.template import Template, loader, Context
from django.http import HttpResponse


def index(request):

    template_name = "ccdataentry/index.html"
    title = "ChildCount-2.0 Data Entry"
    return render_to_response(request, template_name, {
            'title': title,
            'static_path': '/static/ccdataentry/'})

def json(request, source):

    f = open("apps/ccdataentry/static/json_resp/%s" % source, "r")
    raw = f.read()
    f.close()
    h = HttpResponse(raw)
    h._headers['content-type'] = ('Content-Type', 'application/json;')
    return h

    return HttpResponse(raw)
