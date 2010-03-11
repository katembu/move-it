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
        
        #print Location.objects.all()
        self.assertEquals(Location.objects.all().count(), 0)
        ldc = Command()
        filename = os.path.abspath(os.path.join(os.path.dirname(__file__),"fixtures/ruhiira_LocationType"))
        ldc.handle('location', filename)
        filename = os.path.abspath(os.path.join(os.path.dirname(__file__),"fixtures/ruhiira_Locations"))
        ldc.handle('location', filename)
        #print Location.objects.all()
        self.assertEquals(Location.objects.all().count(), 98)
        
    def _register(self):
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

    def testCHWRegistration(self):
        self._register()


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
