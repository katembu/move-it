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



locations = {
    'KR01': [132],
    'KR02': [132],
    'KR03': [69,88],
    'KR04': [87],
    'KR05': [88],
    'KR06': [86],
    'KR07': [86],
    'KR08': [66],
    'KR09': [53],
    'KR10': [87],
    'KR11': [53],
    'KR12': [69,66],
    'KR13': [85],
    'KR14': [85],
    'KR15': [68],
    'KR16': [54],
    'KR17': [118],
    'KR18': [118],
    'KR19': [67],
    'KR20': [67],
    'BG01': [82],
    'BG02': [82],
    'BG03': [82],
    'BG04': [81],
    'BG05': [81],
    'BG06': [84],
    'BG07': [81],
    'BG08': [80],
    'BG09': [80],
    'BG10': [84],
    'BG11': [55],
    'BG12': [55],
    'KG01': [74],
    'KG02': [71],
    'KG03': [74],
    'KG04': [71],
    'KG05': [72,73],
    'KG06': [73],
    'KG07': [70],
    'KG08': [50],
    'KG09': [72],
    'KG10': [70],
    'KG11': [50],
    'KZ01': [92],
    'KZ02': [92],
    'KZ03': [94],
    'KZ04': [94],
    'KZ05': [89],
    'KZ06': [90],
    'KZ07': [112],
    'KZ08': [91],
    'KZ09': [91],
    'KZ10': [91],
    'KZ11': [52],
    'KZ12': [89],
    'KZ13': [93],
    'KZ14': [90],
    'KZ15': [93],
    'NG01': [51],
    'NG02': [51],
    'NG03': [79],
    'NG04': [51],
    'NG05': [79],
    'NG06': [75],
    'NG07': [75],
    'NG08': [76],
    'NG09': [79],
    'NG10': [75],
    'NG11': [76],
    'NG12': [76],
    'NG13': [77],
    'NG14': [77],
    'NG15': [78],
    'NG16': [78],
    'NG17': [78],
    'NG18': [77],
    'RH01': [56],
    'RH02': [63],
    'RH03': [60,58],
    'RH04': [58],
    'RH05': [62,63,56],
    'RH06': [64,61],
    'RH07': [64,60],
    'RH08': [61],
    'RH09': [65],
    'RH10': [65,62],
    'RH11': [62,57],
    'RH12': [57],
    'RH13': [57,59],
    'RH14': [59],
}

from django.db.models import Q

from reversion import revision

from locations.models import Location

from childcount.models import CHW
from childcount.models import Patient
from childcount.models import FormGroup
from childcount.models import Encounter

# For each location
for key in locations:
    code = key
    cids = locations[key]

    print "Trying location %s" % code

    loc = None
    try:
        loc = Location.objects.get(code=code)
    except Location.DoesNotExist:
        print "No location with code [%s]" % code
        continue

    # Get patients in that location
    # who are not assigned to one of 
    # proper CHWs for that location
    patients = Patient\
        .objects\
        .filter(location=loc)\
        .filter(~Q(chw__pk__in=cids))

    for p in patients:
        print "\t%s\t\t%s" % (p, p.chw)

    revision.start()
    patients.update(chw=cids[0])
    revision.end()

    # For each patient set lookup forms that have
    # patient in that encounter
    grps = FormGroup\
        .objects\
        .filter(encounter__patient__in=patients)

    for g in grps:
        print "\t%s" % g

    # Get encounters for these form groups
    encs = map(lambda e: e['encounter'], grps.values('encounter'))
    
    # Set form_group and encounter entered_by to this patient's CHW
    revision.start()
    Encounter\
        .objects\
        .filter(pk__in=encs)\
        .update(chw=cids[0])
    revision.end()

    revision.start()
    grps.update(entered_by=cids[0])
    revision.end()

print "Done!"
