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
from childcount.models import Patient
from ethiopian_date import EthiopianDateConverter
from datetime import datetime
print "Starting..."

patients = Patient.objects.filter(created_on__gte=datetime(2011,04,12,0,0,0))

for i,p in enumerate(patients):

    revision.start()
    new_dob = EthiopianDateConverter.date_to_gregorian(p.dob)
    print "% 7d: <%s> %s ==> %s" % (i, p.health_id.upper(), p.dob, new_dob)
    p.dob = new_dob
    p.save()

    revision.end()

print "Finished!"

