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

from django.db.models import Q,F

from childcount.models import Patient

if len(sys.argv) != 2:
    raise ValueError("Pass file name as only argument")

gisReader = csv.reader(open(sys.argv[1], 'rbU'))

headers = gisReader.next()

seen_codes = set()
seen_people = set()

for row in gisReader:
    code = row[1]
    name = row[3]
    lat = row[13]
    lng = row[14]

    names = name.split()
    last_name = names[0].upper()

    if len(code) != 4:
        print "Skipping %s %s" % (name, code)

    poss = Patient\
        .objects\
        .filter(location__code=code)

    cutoff = 0.4
    matches = difflib.get_close_matches(last_name, \
        [p.last_name.upper() for p in poss], n=1, cutoff=cutoff)

    if matches:
        moposs = poss.filter(last_name=matches[0])

        first_name = ''
        if len(names) > 1:
            first_name = names[1].upper()
        momatches = difflib.get_close_matches(first_name,
            [p.first_name.upper() for p in moposs], n=1, cutoff=cutoff)

        if momatches:
            people = moposs.filter(first_name=momatches[0])

            print "%s | % 4d | %s => %s {%s, %s}" % \
                (code.upper(), poss.count(), name, people, lat, lng)
            people.update(latitude=lat, longitude=lng)
            continue

    if len(names) > 1:
        first_name = names[1].upper()
        matches = difflib.get_close_matches(first_name, \
            [p.last_name.upper() for p in poss], n=1)

        if matches:
            moposs = poss.filter(last_name=matches[0])

            momatches = difflib.get_close_matches(last_name,
                [p.first_name.upper() for p in moposs], n=1)

            if momatches:
                people = moposs.filter(first_name=momatches[0])

                print "%s | % 4d | %s => %s {%s, %s}" % \
                    (code.upper(), poss.count(), name, people, lat, lng)
                people.update(latitude=lat, longitude=lng)
                continue

    print "%s |X% 4d | %s => %s {%s, %s}" % \
        (code.upper(), poss.count(), name, [], lat, lng)


