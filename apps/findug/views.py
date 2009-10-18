#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from datetime import datetime, timedelta

from rapidsms.webui.utils import render_to_response

from models import *
from utils import *
from apps.locations.models import *

from apps.libreport.pdfreport import PDFReport
from apps.libreport.csvreport import CSVReport

def index(req):
    ''' Display Dashboard

    List Alert and conflicts'''

    types    = LocationType.objects.filter(name__startswith="HC")
    locations= Location.objects.filter(type__in=types)
    all = []
    for location in locations:
        loc = {}
        loc['obj']      = location
        all.append(loc)

    return render_to_response(req, 'findug/index.html', {'locations': all})

def locations_view(req):
    ''' List all locations with links to individual pages '''

    clinics  = LocationType.objects.filter(name__startswith="HC")
    locations= Location.objects.filter(type__in=clinics)
    today    = datetime.today()
    all = []
    for location in locations:
        loc = {}
        loc['obj']      = location
        loc['alias']    = location.code.upper()
        all.append(loc)

    # sort by date, descending
    all.sort(lambda x, y: cmp(x['obj'].name, y['obj'].name))
    return render_to_response(req, 'findug/locations.html', { "locations": all})

def location_view(req, location_id):
    ''' Displays a summary of location activities and history '''

    location    = Location.objects.get(id=location_id)

    return render_to_response(req, 'findug/location.html', { "location": location})

def reporters_view(req):
    ''' Displays a list of reporters '''

    def nb_alerts_for(reporter):
        
        return 0

    reporters= Reporter.objects.filter()
    all = []
    for reporter in reporters:
        rep = {}
        rep['obj']      = reporter
        rep['nb_alerts']= nb_alerts_for(reporter)
        rep['up2date']  = rep['nb_alerts'] == 0
        all.append(rep)

    # sort by date, descending
    all.sort(lambda x, y: cmp(x['obj'].alias, y['obj'].alias))
    return render_to_response(req, 'findug/reporters.html', { "reporters": all})

def reporter_view(req, reporter_id):
    ''' Displays a summary of his activities and history '''

    reporter    = Reporter.objects.get(id=reporter_id)

    return render_to_response(req, 'findug/reporter.html', { "reporter": reporter})

def report(req):

    clinics  = LocationType.objects.filter(name__startswith="HC")
    locations= Location.objects.filter(type__in=clinics)
    fields   = []
    fields.append({"name": 'PID#', "column": None, "bit": "{{ object.id }}" })
    fields.append({"name": 'NAME', "column": None, "bit": "{{ object }} {{ object.type }}" })
    
    pdfreport = PDFReport()
    pdfreport.setLandscape(False)
    pdfreport.setTitle("FIND Clinics")
    pdfreport.setTableData(locations, fields, "Table Title")
    pdfreport.setFilename("clinics")

    csvreport = CSVReport()
    csvreport.setLandscape(False)
    csvreport.setTitle("FIND Clinics")
    csvreport.setTableData(locations, fields, "Table Title")
    csvreport.setFilename("clinics")
    

    return csvreport.render()

