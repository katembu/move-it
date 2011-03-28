#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga
from django.contrib.auth.decorators import login_required

from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect, HttpResponse
from django.http import HttpResponseNotFound

from rapidsms.webui.utils import render_to_response

@login_required
def index(request):
    return render_to_response(request, "index.html", {})


