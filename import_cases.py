#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import csv
import codecs
import sys
import re
import datetime

import os
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
    # could be several reasons:
    # no 'contrib' dir, 'contrib' not a dir
    # 'contrib' not readable, in any case
    # ignore and leave 'libs' as just
    # 'rapidsms/lib'
    pass

# add extra libs to the python sys path
sys.path.extend(libs)

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.management import setup_environ
from rapidsms.webui import settings
setup_environ(settings)

from mctc.models import general
from reporters.models import Reporter
from reporters.models import Location

def get_good_date(date):
    delimiters = r"[./\\-]+"
    # expecting DD-MM-YYYY, DD-MM-YY, D-M-YY, etc (with any of the delimiters)
    Allsect=re.split(delimiters,date)            
    if Allsect is not None:
        try:
            year = Allsect[2]
            day = Allsect[0]
            #if day not in range(1,31):
            #    sys.exit('DAY: ' + day)
            month = Allsect[1]         
            if int(month) == 2:
                if int(day) > 28:
                    day = 28
            if int(month) in [4, 6, 9, 11]:
                if int(day) > 30:
                    day = 30
            #if month not in range(1,12):
                #sys.exit('MONTH: ' + month)
            # add leading digits if they are missing
            if len(year) < 4 : 
                year = "20%s" % year        
            if len(month) < 2:
                month = "0%s" % month
            if len(day) == 1:
                day = "0%s" % day         
            if len(day) == 0:
                day = "15"
            good_date_str = "%s-%s-%s" % (int(year),int(month),int(day))
            #good_date_obj = datetime.date(int(year), int(month), int(day))
            return good_date_str
        except Exception, e:
            return None

def age_to_estimated_bday(age_in_months):
    years = int(age_in_months) / 12
    months = int(age_in_months) % 12
    return ("%s-%s-%s" % ((datetime.date.today().year - int(years)),\
                            (datetime.date.today().month - int(months)), 15))
    #return  datetime.date((datetime.date.today().year - years),\
    #                    (datetime.date.today().month - months), 15)


def import_cases_from_csv(csvfile):
    try:
        reporter = Reporter.objects.get(alias='import')
    except (ObjectDoesNotExist, MultipleObjectsReturned):
        sys.exit("Cases require a foreign key relationship with a reporter.\
                    You must create a reporter with alias=import")

    try:
        location = Location.objects.get(code='cmkayar')
    except (ObjectDoesNotExist, MultipleObjectsReturned):
        sys.exit("Cases require a foreign key relationship with a location.\
                    You must create a location with code=cmkayar")

    #csvee = csvfile['content'].split('\n')
    csvee = codecs.open("cayar.csv", "rU", encoding='utf-8', errors='ignore')
    dialect = csv.Sniffer().sniff(csvee.read(1024))
    csvee.seek(0)
    #reader = csv.reader(csvfile, dialect)
    # DictReader uses first row of csv as key for data in corresponding column
    reader = csv.DictReader(csvee, dialect=dialect)

    # keep a list of new cases so we can print progress
    new_cases = []
    try:
        for row in reader:
            case = {}
            #id, name, date_of_birth, age, guardian, guardian_id, guardian_age = line
            #row = {'name' : name, 'date_of_birth' : date_of_birth, 'age' : age,\
            #        'guardian' : guardian, 'guardian_id' : guardian_id}

            if row.has_key('name'):
                first_name, sep, last_name = row['name'].rstrip().rpartition(' ')
                case.update({'last_name' : unicode(last_name, errors='ignore'), 'first_name' : unicode(first_name, errors='ignore')})

            if row.has_key('date_of_birth'):
                try:
                    dob = get_good_date(row['date_of_birth'])
                    case.update({'dob' : dob, 'estimated_dob' : False })
                except Exception, e:
                    sys.exit(e)

            else: 
                if row.has_key('age'):
                    try:
                        case.update({'dob' : get_good_date(age_to_estimated_bday(row['age'])),\
                                        'estimated_dob' : True })
                    except Exception, e:
                        sys.exit(e)
            
            if row.has_key('guardian'):
                case.update({'guardian' : row['guardian']}) 

            if row.has_key('guardian_id'):
                case.update({'guardian_id' : row['guardian_id']})

            case.update({'reporter' : reporter, 'location' : location})

            new_case = general.Case(**case)
            new_case.save()
            new_cases.append(new_case)

    except csv.Error, e:
        # TODO handle this error
        sys.exit('%d : %s' % (reader.reader.line_num, e))


if __name__ == "__main__":
    import_cases_from_csv(sys.argv) 
