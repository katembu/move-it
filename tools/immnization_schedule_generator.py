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

from datetime import datetime, timedelta
from reversion import revision
from childcount.models import Patient
from childcount.models import ImmunizationSchedule
from childcount.models import ImmunizationNotification

revision.start()

''' Generate a schedule for all children under five '''

today = datetime.today()
month_range = timedelta(round(30.4375 * 10))

nine_months = today - month_range

patients = Patient.objects.filter(dob__gte=nine_months)
for patient in patients:
    try:
        schedule = ImmunizationSchedule.objects.all()
    except:
        print u"No immunization schedule existing,Generate schedule from fixtures "
    else:
        '''Generate immunization schedule '''
        for period in schedule:
            patient_dob = patient.dob
            notify_on = datetime.today()
            immunization = ImmunizationNotification()
            if not ImmunizationNotification.objects.filter(patient=patient, \
                                                        immunization=period):
                immunization.patient = patient
                immunization.immunization = period

                if period.period_type == ImmunizationSchedule.PERIOD_DAYS:
                    notify_on = patient_dob + timedelta(period.period)
                    immunization.notify_on = notify_on

                if period.period_type == ImmunizationSchedule.PERIOD_WEEKS:
                    notify_on = patient_dob + timedelta(period.period * 7)
                    immunization.notify_on = notify_on

                if period.period_type == ImmunizationSchedule.PERIOD_MONTHS:
                    notify_on = patient_dob + timedelta(30.4375 * period.period)
                    immunization.notify_on = notify_on

                immunization.save()
                print u"Generating %(imm)s Schedule for %(pat)s " % \
                                    {'pat': patient, 'imm': period}

revision.end()
