#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: rgaudin

from django.conf.urls.defaults import include, patterns, url
from django.contrib import admin
from ccdataentry import views

admin.autodiscover()

try:
    admin_urls = (r'^admin/', include(admin.site.urls))
except AttributeError:
    # Django 1.0 admin site
    admin_urls = (r'^admin/(.*)', admin.site.root)

urlpatterns = patterns('',
    admin_urls,
    url(r'^static/ccdataentry/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': 'apps/ccdataentry/static', 'show_indexes': True}),
    url(r'^ccdataentry/?$', views.index),
    url(r'^ccdataentry/json/(.*)$', views.json ),
)
