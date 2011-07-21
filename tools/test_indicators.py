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
from childcount.models import Patient

from childcount.indicators import follow_up
from childcount.indicators import birth
from childcount.indicators import pregnancy
from childcount.indicators import household
from childcount.indicators import fever
from childcount.indicators import neonatal
from childcount.indicators import under_one
from childcount.indicators import nutrition
from childcount.indicators import danger_signs
from childcount.indicators import bed_net_coverage
from childcount.indicators import bed_net_utilization

from reportgen.timeperiods import Month

###
### END - SETUP RAPIDSMS ENVIRONMENT
###
t = Month.periods()[4]
p = Patient.objects.all()


inds = [danger_signs.UnderFiveDiarrheaUncomplicatedGivenOrsPerc,
            danger_signs.UnderFiveDiarrheaUncomplicatedGivenZincPerc,]

for i in inds:
    print "Testing %s" % i.short_name
    print i(t,p)


