#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import os
from django.conf.urls.defaults import *
import findug.views as views

urlpatterns = patterns('',
    url(r'^findug/$', views.index),
    url(r'^findug/map?$', views.map),
    url(r'^findug/health_units/$', views.health_units_view),
    url(r'^findug/health_unit/(\d+)$', views.health_unit_view),
    url(r'^findug/reporters/$', views.reporters_view),
    url(r'^findug/reporter/(\d+)$', views.reporter_view),
    url(r'^static/findug/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'apps/findug/static', 'show_indexes': True}),
    url(r'^findug/report$', views.report),
    url(r'^findug/epidemiological_report_pdf/(\d+)$', views.epidemiological_report_pdf),
    url(r'^findug/epidemiological_report/(\d+)$', views.epidemiological_report),
)
