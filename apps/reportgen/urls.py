#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.conf.urls.defaults import include, patterns, url
from django.contrib import admin
import webapp

import reportgen.views

urlpatterns = patterns('',
    (r'^reportgen/$', reportgen.views.index),
    url(r'^static/reportgen/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': 'apps/reportgen/static', 'show_indexes': True}),
)
