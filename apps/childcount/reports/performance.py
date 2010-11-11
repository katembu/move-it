#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

import time
import datetime

from django.utils.translation import gettext_lazy as _

from rapidsms.webui.utils import render_to_response

from childcount.models.ccreports import TheCHWReport

def chw_performance(request):
    context_dict = {}
    chws = TheCHWReport.objects.filter(is_active=True).all()[10:15]
    context_dict['chws'] = chws

    return render_to_response(request, \
        'childcount/reports/performance.html', \
        context_dict)
    


