#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import os

from django.conf.urls.defaults import include, patterns, url
from django.contrib import admin
import webapp

import reportgen.views

urlpatterns = patterns('',
    (r'^reportgen/$', reportgen.views.index),
    (r'^reportgen/nightly/$', reportgen.views.nightly),
    (r'^reportgen/ondemand/$', reportgen.views.ondemand),
    url(r'^static/reportgen/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': '%s/static' % os.path.dirname(__file__),
                'show_indexes': False}),
)
