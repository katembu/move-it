#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import os

from django.conf.urls.defaults import include, patterns, url
from django.contrib import admin
import webapp

from childcount import views
from childcount.reports import pmtct
from childcount.reports import custom_reports as reports
from childcount.reports import report_framework  

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

    # webapp URLS
    url(r'^accounts/login/$', "webapp.views.login", \
                     {'template_name': 'childcount/login.html'}, name='login'),
    url(r'^accounts/logout/$', "webapp.views.logout", \
                {'template_name': 'childcount/loggedout.html'}, name='logout'),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url('^static/webapp/(?P<path>.*)$', 'django.views.static.serve', \
        {'document_root': '%s/static' % os.path.dirname(webapp.__file__)}),

    url(r'^$', views.index, name='dashboard'),
    url(r'^childcount/?$', views.index, name='cc-dashboard'),
    url(r'^childcount/patients/?$', views.patient, name='cc-patients'),
    url(r'^childcount/patients/edit/((?P<healthid>[A-Z0-9]+)/)?$',
        views.edit_patient, name='cc-edit_patient'),
    #url(r'^childcount/patients/autocomplete/$',
    #    views.autocomplete),
    url(r'^childcount/patients/(?P<page>\d+)/?$', views.patient),
    url(r'^childcount/bednet/?$', views.bednet_summary),

    url(r'^childcount/patients_per_chw/pdf/?$', \
                                    reports.all_patient_list_per_chw_pdf),
    url(r'^childcount/chw/?$', views.chw),
    url(r'^childcount/chws/(?P<rformat>[a-z]*)$', reports.chw),
    url(r'^childcount/under_five', reports.under_five),

    url(r'^childcount/add_chw/?$', views.add_chw, name='cc-add_chw'),
    url(r'^childcount/list_chw/?$', views.list_chw, name='cc-list_chw'),

    url(r'^childcount/dataentry/?$', views.dataentry, name='cc-dataentry'),
    url(r'^childcount/dataentry/form/(?P<formid>[a-zA-Z0-9\-\_\.]*)/?$', \
                        views.form, name='form'),
    url(r'^childcount/site_summary/(?P<report>[a-z_]*)/(?P<format>[a-z]*)$', \
        views.site_summary),

    # PMTCT links
    url(r'^childcount/reports/pmtct-defaulters/(?P<rformat>[a-z]*)$', 
        pmtct.defaulters),
    url(r'^childcount/reports/pmtct-deliveries/(?P<rformat>[a-z]*)$', 
        pmtct.upcoming_deliveries),
    url(r'^childcount/reports/pmtct-newregs/(?P<rformat>[a-z]*)$', 
        pmtct.new_registrations),
    url(r'^childcount/reports/pmtct-mothers-onfollowup/(?P<rformat>[a-z]*)$', 
        pmtct.active_mothers),
    url(r'^childcount/reports/pmtct-stats/(?P<rformat>[a-z]*)$', 
        pmtct.statistics),

    # On-Demand Reports for Reporting Framework
    url(r'^childcount/reports/ondemand/(?P<rname>[a-zA-Z0-9\-\_]*).(?P<rformat>[a-z]*)$', 
        report_framework.serve_ondemand_report),
)
