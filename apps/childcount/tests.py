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
    App.FORMS = [PatientRegistrationForm, MUACForm, HealthStatusForm, FeverForm, MobileForm, NewbornForm, ChildForm, HouseHoldVisitForm, PregnancyForm, PostpartumForm, ReferralForm, DeathForm, DispensationForm]
    App.COMMANDS = [WhoCommand, RegistrationCommand]
    fixtures = ['uganda_locations', 'uganda_locations_type']

    def testAll(self):
        #print Location.objects.all()
        self.assertEquals(Location.objects.all().count(), 0)
        ldc = Command()
        filename = os.path.abspath(os.path.join(os.path.dirname(__file__),"fixtures/uganda_locations_type"))
        ldc.handle('location', filename)
        filename = os.path.abspath(os.path.join(os.path.dirname(__file__),"fixtures/uganda_locations"))
        ldc.handle('location', filename)
        #print Location.objects.all()
        self.assertEquals(Location.objects.all().count(), 98)
        
        testRegister = """
            123 > who
            123 < 123 is not a registered number.
            123 > chw bidxcvxxx lname fname
            123 < Location bidxcvxxx does not exist
            123 > chw bir lname fname
            123 < Success. You are now registered at Birare with alias @flname.
        """
        self.runScript(testRegister)

        chw = CHW.objects.get(alias='flname')
        self.assertEqual(chw.first_name, 'Fname')

        testWho = """
            123 > who
            123 < You are registered as Fname Lname from Birare with alias @flname.
        """
        self.runScript(testWho)

        testForms = """
            123 > d47q +a 2 +r c
            123 < D47Q is not a valid health ID. Please correct and send forms for that patient again.
            123 > d47q +new jane mini f 110984 p +mob 0727944684
            123 < D47Q: You successfuly registered D47Q Jane Mini F/25y \+MOB[0727944684]
            #123 > d47q +new jane mini f 110984 p +mob 0727944684
            #123 < Form +NEW failed: Jane Mini F/25y was already registered by you. Their health id is D47Q
            #123 < D47Q is not a valid health ID. Please correct and send forms for that patient again.
            123 > D4A1 +New odhiambo moses 200509 magret awino
            123 < Form +NEW failed: You must indicate gender after the name with a M or F
            123 < D4A1 is not a valid health ID. Please correct and send forms for that patient again.
        """
        self.runScript(testForms)

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
