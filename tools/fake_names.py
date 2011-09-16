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
from childcount.models import Patient, HealthId
from datetime import datetime
import faker
import random


print "Starting..."

patients = Patient.objects.filter(chw__first_name='Annet')
for i,p in enumerate(patients):
    nids = HealthId.objects.filter(status='G').count()
    print p.health_id.upper()
    p.first_name = faker.name.first_name()
    p.last_name = faker.name.last_name()
    p.gender = random.choice(['M', 'F'])

    try:
        h1 = HealthId.objects.get(health_id=p.health_id)
        h1.status = 'G'
        h1.save()
    except:
        pass

    p.health_id = HealthId\
        .objects\
        .filter(status='G')[random.randint(0, nids)].health_id
    h = HealthId.objects.get(health_id=p.health_id)
    h.status = 'A'
    h.save()

    if p.is_head_of_household():
        p.dob = faker.date.birthday(average=35, min=18, max=70)
    else:
        p.dob = faker.date.birthday(average=18, min=0, max=70)

    p.save()

print "Finished!"

