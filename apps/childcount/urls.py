from django.conf.urls.defaults import *
from django.contrib import admin
import childcount.views as views

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
    url(r'^childcount/reports?$', views.reports),
    (r'^report/(?P<report_name>[a-z\-\_]+)/(?P<object_id>\d*)$', "childcount.views.report_view"),
    #last_30_days
    (r'^last_30_days/$', "childcount.views.last_30_days"),
    (r'^last_30_days/(?P<object_id>\d*)$', "childcount.views.last_30_days"),
    (r'^last_30_days/per_page/(?P<per_page>\d*)$', "childcount.views.last_30_days"),
    (r'^last_30_days/per_page/(?P<per_page>\d*)/(?P<d>\d*)$', "childcount.views.last_30_days"),
    #patients_by_chw
    (r'^patients_by_chw/$', "childcount.views.patients_by_chw"),
    (r'^patients_by_chw/(?P<object_id>\d*)$', "childcount.views.patients_by_chw"),
    (r'^patients_by_chw/per_page/(?P<per_page>\d*)$', "childcount.views.patients_by_chw"),
    (r'^patients_by_chw/(?P<object_id>\d*)/(?P<rformat>[a-z]*)$', "childcount.views.patients_by_chw"),
    #last_30_days
    (r'^measles_summary/$', "childcount.views.measles_summary"),
    (r'^measles_summary/(?P<object_id>\d*)$', "childcount.views.measles_summary"),
    (r'^measles_summary/per_page/(?P<per_page>\d*)$', "childcount.views.measles_summary"),
    (r'^measles_summary/per_page/(?P<per_page>\d*)/(?P<d>\d*)$', "childcount.views.measles_summary"),
    #patients_by_chw
    (r'^measles/$', "childcount.views.measles"),
    (r'^measles/(?P<object_id>\d*)$', "childcount.views.measles"),
    (r'^measles/per_page/(?P<per_page>\d*)$', "childcount.views.measles"),
    (r'^measles/(?P<object_id>\d*)/(?P<rformat>[a-z]*)$', "childcount.views.measles"),
    #patients_by_chw
    (r'^malaria/$', "childcount.views.malaria"),
    (r'^malaria/(?P<object_id>\d*)$', "childcount.views.malaria"),
    (r'^malaria/per_page/(?P<per_page>\d*)$', "childcount.views.malaria"),
    (r'^malaria/(?P<object_id>\d*)/(?P<rformat>[a-z]*)$', "childcount.views.malaria"),
    #patients_by_chw
    (r'^malnut/$', "childcount.views.malnut"),
    (r'^malnut/(?P<object_id>\d*)$', "childcount.views.malnut"),
    (r'^malnut/per_page/(?P<per_page>\d*)$', "childcount.views.malnut"),
    (r'^malnut/(?P<object_id>\d*)/(?P<rformat>[a-z]*)$', "childcount.views.malnut"),
    #patients_by_chw
    (r'^trend/$', "childcount.views.trend"),
    (r'^trend/(?P<object_id>\d*)$', "childcount.views.trend"),
    (r'^trend/per_page/(?P<per_page>\d*)$', "childcount.views.trend"),
    (r'^trend/(?P<object_id>\d*)/(?P<rformat>[a-z]*)$', "childcount.views.trend"),
    #patients_by_age
    (r'^List_Enfant_Age/$', "childcount.views.patients_by_age"),
    (r'^List_Enfant_Age/(?P<object_id>\d*)$', "childcount.views.patients_by_age"),
    (r'^List_Enfant_Age/per_page/(?P<per_page>\d*)$', "childcount.views.patients_by_age"),
    (r'^List_Enfant_Age/(?P<object_id>\d*)/(?P<rformat>[a-z]*)$', "childcount.views.patients_by_age"),
    # commands shortlist
    (r'^childcount/commands-shortlist', "childcount.views.commands_pdf"),
    #malnutrition_screening
    (r'^malnutrition_screening/$', "childcount.views.malnutrition_screening"),
)

