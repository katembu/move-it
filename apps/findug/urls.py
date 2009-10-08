#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import os
from django.conf.urls.defaults import *
import findug.views as views

urlpatterns = patterns('',
    url(r'^findug/?$', views.index),
    url(r'^findug/locations/?$', views.locations_view),
    url(r'^findug/location/(\d+)$', views.location_view),
    url(r'^findug/reporters/?$', views.reporters_view),
    url(r'^findug/reporter/(\d+)$', views.reporter_view),
    url(r'^static/findug/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'apps/findug/static', 'show_indexes': True}),
)
