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

from childcount.models import Patient
from childcount.models.reports import FeverReport
from childcount.models.reports import DangerSignsReport

gisWriter = csv.writer(sys.stdout)

ps = Patient.objects.filter(latitude__isnull=False,\
                            longitude__isnull=False)

rows = FeverReport\
    .objects\
    .filter(encounter__patient__household__latitude__isnull=False,
            encounter__patient__household__longitude__isnull=False)

for p in ps:

    fevers = DangerSignsReport\
        .objects\
        .filter(encounter__patient__household=p,\
                danger_signs__code__in=['FV'])\
        .count()

    diarrheas = DangerSignsReport\
        .objects\
        .filter(encounter__patient__household=p,\
                danger_signs__code__in=['DR'])\
        .count()

    gisWriter.writerow([p.latitude, 
                        p.longitude,
                        fevers,
                        diarrheas])
                        
