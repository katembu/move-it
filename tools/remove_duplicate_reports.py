#!/usr/bin/python


###
### START - SETUP RAPIDSMS ENVIRONMENT
###

import sys, os
from os import path

# figure out where all the extra libs (rapidsms and contribs) are
libs=[os.path.abspath('lib'),os.path.abspath('apps')] # main 'rapidsms/lib'
try:
    for f in os.listdir('contrib'):
        pkg = path.join('contrib',f)
        if path.isdir(pkg) and \
                'lib' in os.listdir(pkg):
            libs.append(path.abspath(path.join(pkg,'lib')))
except:
    pass

# add extra libs to the python sys path
sys.path.extend(libs)
path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(path)

os.environ['RAPIDSMS_INI'] = os.path.join(path, "local.ini")
os.environ['DJANGO_SETTINGS_MODULE'] = 'rapidsms.webui.settings'
# import manager now that the path is correct
from rapidsms import manager
from django.db import IntegrityError
from childcount.models import HealthId
###
### END - SETUP RAPIDSMS ENVIRONMENT
###


from reversion import revision
from childcount.models.reports import CCReport
from childcount.models import Encounter
from datetime import datetime

def r_query(report):
    q = []
    for f in report._meta.fields:
        if f.name not in ['id','ccreport_ptr']:
            q.append((f.name+'__exact', getattr(report, f.name)))
    return q

def print_rep(report):
    for f in report._meta.fields:
        print "\t%s = %s" % (f.name, getattr(report,f.name))

i = 0
for e in Encounter.objects.all():
    i += 1
    if i%100==0:
        print "Working on encounter %d" % e.pk
  
    count = e.ccreport_set.count()
    while True:
        for r in e.ccreport_set.all():
            query = r_query(r)
            # Look for a duplicate report for the same name
            dups = r.__class__.objects.exclude(pk=r.pk).filter(*query)
            if dups.count() > 0:
                print "DUP: [%s] [%s]" % (map(lambda d: d.encounter.pk,dups), r.encounter.pk)
                print_rep(r)
                for d in dups:
                    print_rep(d)
                # If we find one, delete this record (leave the duplicate)
                r.delete()

        # Loop until we don't find an encounter to delete
        if count == e.ccreport_set.count():
            break
        count = e.ccreport_set.count()

