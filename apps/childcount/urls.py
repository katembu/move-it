#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: ukanga

import os

from django.conf.urls.defaults import include, patterns, url
from django.contrib import admin
import webapp

from childcount import views

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
    url(r'^moveit/?$', views.index, name='cc-dashboard'),

    url(r'^moveit/chws.json/?$', views.chw_json),
    url(r'^moveit/add_chw/?$', views.add_chw, name='cc-add_chw'),
    url(r'^moveit/list_chw/?$', views.list_chw, name='cc-list_chw'),

    url(r'^moveit/dataentry/?$', views.dataentry, name='cc-dataentry'),
    url(r'^moveit/dataentry/form/(?P<formid>[a-zA-Z0-9\-\_\.]*)/?$', \
                        views.form, name='form'),

    url(r'^moveit/status/((?P<eventid>[a-zA-Z0-9]+)/)?$', \
                views.status_update, name='cc-status-update'),

    url(r'^moveit/register/((?P<eventtype>[a-zA-Z0-9]+)/)?$', \
                views.register, name='cc-register'),
    url(r'^moveit/register/edit/((?P<eventid>[a-zA-Z0-9]+)/)?$',
        views.register_edit, name='cc-edit_patient'),


)
