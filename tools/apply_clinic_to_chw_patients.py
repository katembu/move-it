#!/usr/bin/python

# Since in Sauri the location was the clinic that the chw was tied to, 
# we need to attach a clinic object to the chw as well as associate the 
# patients of the chw to the clinic the chw belongs to as that is techinically
# the clinic they will be going to

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


from reversion import revision
from childcount.models import Clinic
from childcount.models import CHW
from childcount.models import Patient

revision.start()

c = 0
for chw in CHW.objects.all():
    try:
        clinic = Clinic.objects.get(pk=chw.location.pk)
        if clinic == chw.clinic:
            continue
    except Clinic.DoesNotExist:
        print chw, chw.location
        pass
    except:
        print chw
        pass
    else:
        chw.clinic = clinic
        chw.save()
        c += 1

        for patient in Patient.objects.filter(chw=chw):
            patient.clinic = clinic
            patient.save()
        print u"Changed: %d patients" % Patient.objects.filter(chw=chw).count()
print "%d CHWs clinic changed out of the total %d CHWs" % \
                                                (c, CHW.objects.all().count())
revision.end()

