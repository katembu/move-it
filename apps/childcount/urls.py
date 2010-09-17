#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

from django.conf.urls.defaults import include, patterns, url
from django.contrib import admin

import childcount.views as views
import childcount.reports.old_reports as old_reports
import childcount.reports.statistics as statistics
import childcount.reports.lists as lists

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
    url(r'^childcount/?$', views.index),
    url(r'^childcount/patients/?$', views.patient),
    url(r'^childcount/patients/(?P<page>\d+)/?$',views.patient),
    url(r'^childcount/bednet/?$', views.bednet_summary),
    url(r'^childcount/patients/(?P<rfilter>[a-z]+)/(?P<rformat>[a-z]+)?$', \
        old_reports.all_patient_list_pdf),
    url(r'^childcount/patients_per_chw/pdf/?$', \
        old_reports.all_patient_list_per_chw_pdf),
    url(r'^childcount/chw/?$', views.chw),
    url(r'^childcount/chws/(?P<rformat>[a-z]*)$',
        old_reports.chw),
    url(r'^childcount/under_five',
        old_reports.under_five),
    url(r'^childcount/operationalreport/(?P<rformat>[a-z]*)$', \
        old_reports.operationalreport),
    url(r'^childcount/registerlist/(?P<clinic_id>\d+)$',
        old_reports.registerlist),
    
    url(r'^childcount/reports/form_a_entered/(?P<rformat>[a-z]*)$',
       statistics.form_a_entered, name='form_a_entered'),
    url(r'^childcount/reports/form_b_entered/(?P<rformat>[a-z]*)$',
       statistics.form_b_entered, name='form_b_entered'),

    url(r'^childcount/reports/patient_list_geo/(?P<rformat>[a-z]*)$',
       lists.patient_list_geo, name='patient_list_geo'),

    url(r'^childcount/add_chw/?$', views.add_chw, name='add_chw'),
    url(r'^childcount/list_chw/?$', views.list_chw, name='list_chw'),

    url(r'^childcount/dataentry/?$', views.dataentry, name='dataentry'),
    url(r'^childcount/dataentry/form/(?P<formid>[a-zA-Z0-9\-\_\.]*)/?$', \
                        views.form, name='form'),
)
