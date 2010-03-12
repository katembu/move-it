import os

from rapidsms.tests.scripted import TestScript
from django.core.management.commands.loaddata import Command

import reporters.app as reporter_app
import locations.app as locations_app

from locations.models import *
from childcount.models import CHW

from app import App
from childcount.forms import *
from childcount.commands import *


class TestApp (TestScript):
    apps = (reporter_app.App, locations_app.App, App,)
    App.forms = [PatientRegistrationForm, BirthForm, MobileForm, DeathForm, StillbirthMiscarriageForm, FollowUpForm, PregnancyForm, NeonatalForm, UnderOneForm, NutritionForm, FeverForm, ReferralForm, DangerSignsForm, MedicineGivenForm, HouseHoldVisitForm, FamilyPlanningForm, BedNetForm]
    App.commands = [WhoCommand, RegistrationCommand]
    fixtures = ['uganda_locations', 'uganda_locations_type']

    def setUp(self):
        super(TestApp, self).setUp()

        
    def _register(self):
        #print Location.objects.all()
        self.assertEquals(Location.objects.all().count(), 0)
        ldc = Command()
        filename = os.path.abspath(os.path.join(os.path.dirname(__file__),"fixtures/ruhiira_LocationType"))
        ldc.handle('location', filename)
        filename = os.path.abspath(os.path.join(os.path.dirname(__file__),"fixtures/ruhiira_Locations"))
        ldc.handle('location', filename)
        #print Location.objects.all()
        self.assertEquals(Location.objects.all().count(), 98)
        self.runScript("""
            123 > chw bir lname fname
            123 < Success. You are now registered at Birare with alias @flname.
            123 > who
            123 < You are registered as Fname Lname from Birare with alias @flname.
        """)

    def test_registration_fails(self):
        self.runScript("""
            123 > who
            123 < 123 is not a registered number.
            123 > chw bidxcvxxx lname fname
            123 < Location bidxcvxxx does not exist
        """)
    '''
    def testCHWRegistration(self):
        self._register()
    '''

    def testYouMustBeRegistered(self):
        self.runScript("""
            123 > d345 +new bir mary unding f 19730512 p +mob 0720395121
            123 < You must register before you can send any reports.
        """)

    def testPatientRegistration(self):
        self._register()
        self.runScript("""
        123 > d345 +new bir mary unding f 19730512 p +mob 0720395121
        123 < Error while processing +NEW: Could not understand age or date_of_birth of 19730512 - Please correct and send all information again.
        123 > d345 +new bir mary unding f 12051973 p +mob 0720395121
        123 < +NEW, +MOB successfuly processed: [You successfuly registered D345 Mary Unding F/36y] [Mobile phone number: 0720395121]
        123 > d346 +new bir baby mary m 23022009 d345 d345
        123 < +NEW successfuly processed: [You successfuly registered D346 Baby Mary M/12m]
        """)

        #test forms
        self.runScript("""
            123 > +d346 +v y 1
            123 < Error: Could not understand your message. Your message must start with a single health ID, followed by a space then a + then the form keyword you are sending.
            123 > d346 +v y 1
            123 < +V successfuly processed: [Household member available, 1 children under 5 seen]
            123 > d346 +v y 1 ed nut
            123 < +V successfuly processed: [Household member available, 1 children under 5 seen, counseling / advice topics covered: General education, Nutrition]
        """)

    # define your test scripts here.
    # e.g.:
    #
    # testRegister = """
    #   8005551212 > register as someuser
    #   8005551212 < Registered new user 'someuser' for 8005551212!
    #   8005551212 > tell anotheruser what's up??
    #   8005550000 < someuser said "what's up??"
    # """
    #
    # You can also do normal unittest.TestCase methods:
    #
    # def testMyModel (self):
    #   self.assertEquals(...)
