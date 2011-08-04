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

from django.db.models import Q

from locations.models import Location

from childcount.models import DeadPerson
from childcount.models.reports import DeathReport

gisWriter = csv.writer(sys.stdout)

ls = Location.objects.all()
gisWriter.writerow([
    "LOC_CODE",
    "DATE_OF_BIRTH",
    "DATE_OF_DEATH",
])
for l in ls:
    ps = DeadPerson.objects.filter(dod__gte='2010-06-01',
                            dod__lte='2011-05-31',\
                            household__location=l)
    for p in ps:
        gisWriter.writerow([l.code.upper(),
                            p.dob,
                            p.dod])

    ps = DeathReport.objects.filter(death_date__gte='2010-06-01',
                            death_date__lte='2011-05-31',
                            encounter__patient__location=l)

    for p in ps:
        gisWriter.writerow([p.encounter.patient.location.code.upper(),
                            p.encounter.patient.dob,
                            p.death_date])
                        
