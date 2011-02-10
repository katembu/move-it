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
from childcount.models import Patient, Encounter
from datetime import datetime

def combine_encs(lst):
    print "Combining encounters: " 

    new = lst[0]
    old = lst[1:]

    for e in lst:
        print "\t%s %s %s [New: %d] [Old: %s]" % (e.type, e.encounter_date, e.patient.health_id.upper(),\
            new.pk, ','.join(map(lambda q: '%d'%q.pk, old)))

    for e in old:
        e.ccreport_set.update(encounter=new)
        e.formgroup_set.update(encounter=new)
        e.delete()

revision.start()
i = 0
for p in Patient.objects.all():
    i += 1
    if i%100==0:
        print "Working on patient %s" % p.health_id.upper()
    for t in Encounter.TYPE_CHOICES:
        enc_set = p.encounter_set.filter(type=t[0]).order_by('encounter_date')
        dates = map(lambda v: v['encounter_date'], enc_set.values('encounter_date').distinct())
        for d in dates:
            to_combine = enc_set.filter(encounter_date = d)
            if to_combine.count() > 1:
                combine_encs(to_combine)

revision.end()

