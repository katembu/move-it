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

###
### END - SETUP RAPIDSMS ENVIRONMENT
###

import csv
import difflib
import pprint
import string
import sys
import urllib

from django.db.models import Q

from childcount.models import Patient
from childcount.models.reports import DangerSignsReport

def get_alt(people):
    lats = ','.join([str(p['latitude']) for p in people.values('latitude')])
    lngs = ','.join([str(p['longitude']) for p in people.values('longitude')])

    url = "http://api.geonames.org/astergdem?"\
            "lats=%s&lngs=%s"\
            "&username=henrycg" % (lats, lngs)
    data = urllib.urlopen(url).read()

    elvs = data.split()
    for i,p in enumerate(people):
        p.elevation = elvs[i]
        p.save()
        print "%s,%s" % (p.health_id.upper(), elvs[i])
    return


people = Patient.objects.filter(latitude__isnull=False,\
                                longitude__isnull=False,\
                                elevation__isnull=False)
"""
elvs = {}

for p in people:
    if p.elevation in elvs:
        elvs[p.elevation] += 1
    else:
        elvs[p.elevation] = 1

print "ELEVATION,POP"

for e in elvs:
    print "%s,%d" % (str(e), elvs[e])
"""

for i in xrange(1250, 1700, 50):
    ps = DangerSignsReport\
        .objects\
        .filter(encounter__patient__household__elevation__gte=i,
            encounter__patient__household__elevation__lt=i+50,
            danger_signs__code__in=["FV"])\
        .count()

    print "%d,%d" % (i, ps)

