#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.conf.urls.defaults import include, patterns, url
from django.contrib import admin

import childcount.views as views
import childcount.reports as reports

admin.autodiscover()

# an issue between Django version 1.0 and later?
# see http://code.djangoproject.com/ticket/10050
try:
    admin_urls = (r'^admin/', include(admin.site.urls))
except AttributeError:
    # Django 1.0 admin site
    admin_urls = (r'^admin/(.*)', admin.site.root)

urlpatterns = patterns('',
    admin_urls,
    url(r'^static/childcount/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': 'apps/childcount/static', 'show_indexes': True}),
    url(r'^childcount/?$', views.index),
    url(r'^childcount/patients/?$', views.patient),
    url(r'^childcount/patients/pdf/?$', reports.all_patient_list_pdf),
    url(r'^childcount/chw/?$', views.chw)

)
