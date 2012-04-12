#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

import re, random
from datetime import date, datetime

from django.db import models
from django.utils.translation import ugettext as _

from django.db.models import Q

from locations.models import Location

from childcount.utils import clean_names, DOBProcessor, random_id
from childcount.utils import send_alert, authenticated, servelet

from childcount.models import Configuration
from childcount.models import Patient, CHW as CHWES

from childcount.exceptions import BadValue, ParseError

from childcount.forms.utils import MultipleChoiceField
from childcount.commands import CCCommand

class BirthRegistrationCommand(CCCommand):
    """ Register a new Birth
    Params:
        * location
        * names
        * gender
        * age or DOB
        * Place
        * Notification Number
        * Mobile
    """

    KEYWORDS = {
        'en': ['birth', 'bir', 'birth!'],
    }
  
    OVERIDE_KEYWORDS = ['birth!']

    MULTIPLE_PATIENTS = False

    gender_field = MultipleChoiceField()
    gender_field.add_choice('en', Patient.GENDER_MALE, 'M')
    gender_field.add_choice('en', Patient.GENDER_FEMALE, 'F')


    place_field = MultipleChoiceField()
    place_field.add_choice('en', Patient.HEALTH_FACILITY, 'C')
    place_field.add_choice('en', Patient.HOME_FACILITY, 'H')

    SURNAME_FIRST = False


    @authenticated
    def process(self):
        chw = self.message.reporter.chw
        lang = self.message.reporter.language
        birth = Patient()
        birth.chw = chw
        #Check if CHW has permission i.e Chief, Assistant Chief
        allowed_groups = ("Assistant Chief", "CHW", "Chief")
        reporters = CHWES.objects.filter(user_ptr__groups__name__in=allowed_groups)

        if chw not in reporters:
            raise ParseError(_(u"Youre not allowed to report Events "))



        expected = _(u"location | child names | gender | DOB | place | mobile")
        if len(self.params) < 7:
            raise ParseError(_(u"Not enough information. Expected: " \
                                "%(keyword)s %(expected)s") % \
                                {'keyword': self.params[0], \
                                'expected': expected})


        #event id
        birth.health_id = random_id()

        #Event Type
        birth.event_type = Patient.BIRTH

        tokens = self.params[1:]

        #check if allowed to report for this location
        if chw.assigned_location.all().count() == 0:
            raise BadValue(_(u"Youve not been assigned any location. " \
                                "Contact District Registry "))

        if chw.assigned_location.all().count() > 1:
            location_code = tokens.pop(0)
            try:
                location = Location.objects.get(code__iexact=location_code)
            except Location.DoesNotExist:
                raise BadValue(_(u"Youre assigned more than one location. " \
                                  "Please specify a valid location code " \
                                  "before name. %(loc)s is not a valid " \
                                  "location code.") %  \
                                 {'loc': location_code.upper()})

        else:
            location = chw.assigned_location.all()[0]

        birth.location = location

        self.gender_field.set_language(lang)

        gender_indexes = []
        i = 0
        for token in tokens:
            if token in self.gender_field.valid_choices():
                gender_indexes.append(i)
            i += 1

        if len(gender_indexes) == 0:
            raise ParseError(_(u"You must indicate gender after the name " \
                                "with a %(choices)s.") % \
                              {'choices': self.gender_field.choices_string()})

        dob = None
        for i in gender_indexes:
            # the gender field is at the end of the tokens.  We don't know
            # what to do about this.
            if i == len(tokens) - 1:
                raise ParseError(_(u"Message not understood. Expected: " \
                                    "%(expected)s") % \
                                    {'expected': expected})

            dob, variance = DOBProcessor.from_age_or_dob(lang, tokens[i + 1], \
                                                         self.date.date())


            if dob:
                birth.dob = dob

                days, weeks, months = birth.age_in_days_weeks_months(\
                    self.date.date())
                
                humanised = birth.humanised_age()

                if days > 90:
                    raise BadValue(_(u"Birth is %(age)s old. You can not " \
                                          "submit birth reports for child over " \
                                          "90 days old.") % {'age': humanised})
                if days < 60 and variance > 1:
                    raise BadValue(_(u"You must provide an exact birth date " \
                                      "for children under 2 months."))
                elif months < 24 and variance > 30:
                    raise BadValue(_(u"You must provide an exact birth date " \
                                      "or the age, in months, for children " \
                                      "under two years."))
                elif birth.dob > date.today():
                    raise BadValue(_("The birth date you gave %(bdate)s) " \
                                     "is in the future!  Please try reentering " \
                                     "the date with the full year " \
                                     "(like 2011  instead of 09).") % \
                                     {'bdate': birth.dob.strftime('%d-%b-%Y')})

        if not dob:
            raise ParseError(_(u"Could not understand age or " \
                                    "date_of_birth of %(string)s.") % \
                                    {'string': tokens[i + 1]})

        birth.estimated_dob = variance > 1

        # if the gender field is the first or second
        if i == 0:
            raise ParseError(_(u"You must provide a birth name before " \
                                "their sex."))

        birth.last_name, birth.first_name, alias = \
                             clean_names(' '.join(tokens[:i]), \
                             surname_first=self.SURNAME_FIRST)

        # remove the name tokens
        tokens = tokens[i:]

        # remove the gender token
        birth.gender = self.gender_field.get_db_value(tokens.pop(0))

        # remove the age token
        tokens.pop(0)

        '''
        Place the birth occured
        If place of birth is hospital expect notification number or (U) Unknown
        '''
        if(len(tokens) < 2):
            raise ParseError(_(u"Not enough information. Expected: " \
                                "%(keyword)s %(expected)s") % \
                                {'keyword': self.params[0], \
                                'expected': expected})
        
        self.place_field.set_language(lang)

        token = tokens[0]
        if token not in self.place_field.valid_choices():
            raise ParseError(_(u"You must indicate place after the Date of  " \
                                "birth with a %(choices)s.") % \
                              {'choices': self.place_field.choices_string()})

        #Remove the place token
        birth.place = self.place_field.get_db_value(tokens.pop(0))
        
        #notification number
        if birth.place == Patient.HEALTH_FACILITY:
            if(len(tokens) < 2):
                raise ParseError(_(u"You must indicate notification number  " \
                               "if place is clinic or U for not issued/Unkown"))
            #Notification number
            noti_number = ''.join(tokens[0])
            #noti_number = re.sub('\D', '', noti_number)
            if not noti_number.isdigit():
                if noti_number != 'u' or noti_number != 'U':
                    raise BadValue(_(u"Invalid notification Number."))

            if len(noti_number) > 10:
                raise BadValue(_(u"Notification number cannot be longer "\
                                  "than 10 digits."))
            if noti_number.upper() != Patient.CERT_UNVERIFIED:    
                birth.notification_no = noti_number
                birth.cert_status = Patient.CERT_VERIFIED        
                
            #Remove the notification token
            tokens.pop(0)
        
        #Mobile number
        mob = ''.join(tokens[0:])
        mob = re.sub('\D', '', mob)
        if not mob.isdigit():
            raise BadValue(_(u"Expected: phone number."))

        if len(mob) < 10:
            raise BadValue(_(u"Phone number is too short"))
        if len(mob) > 16:
            raise BadValue(_(u"Phone number is too long"))

        birth.mobile = mob

        #Counter check if birth exist
        birth_check = Patient.objects.filter( \
                                first_name__iexact=birth.first_name, \
                                last_name__iexact=birth.last_name, \
                                dob=birth.dob, event_type = Patient.BIRTH)

        if len(birth_check) > 0:
            old_p = birth_check[0]
            if old_p.chw == chw:
                birth_chw = _(u"you")
            else:
                birth_chw = birth_check[0].chw
            #override if it is a different CHW and they used the override
            if self.params[0] in self.OVERIDE_KEYWORDS and \
                        old_p.chw != chw:
                pass
            else:
                raise BadValue(_(u"%(name)s %(sex)s/%(age)s was already " \
                              "registered by %(chw)s. Their Event_id is " \
                              "%(id)s.") % \
                              {'name': old_p.full_name(), \
                               'sex': old_p.gender, \
                               'age': old_p.humanised_age(), \
                               'chw': birth_chw, \
                               'id': old_p.health_id.upper()})
        birth.save()

        self.message.respond(_("You successfuly reported the birth of" \
                                " %(birth)s, %(gender)s %(age)s in %(loc)s "\
                                 "and EventId is: %(evnt)s ") %  
                                    {'birth': birth, \
                                     'gender': birth.get_gender_display(), \
                                      'evnt': birth.health_id.upper(), \
                                      'loc': birth.location.name, \
                                      'age': birth.humanised_age()})




        #Send alert to chief (Chief can be CHW )
        groups = ("Assistant Chief", "Chief")
        chief = False
  
        try:
            chief = CHWES.objects.exclude(pk=chw.pk).filter( \
                                        user_ptr__groups__name__in=groups, \
                                         assigned_location=birth.location)[0]

            #chief =  chief.filter(~Q(pk=chw.pk))[0]
        except IndexError:
            print "CHIEF DOESNOT EXIST "
            pass

        if chief and chief != chw:
            if birth.notification_no == Patient.CERT_UNVERIFIED:
                msg = _(u"%(child)s, %(gender)s %(age)s, in %(location)s " \
                            "EventId: %(evnt)s CHW no" \
                            ":%(mobile)s") % \
                         {'child': birth, \
                          'gender': birth.get_gender_display(), \
                          'location': birth.location.name, \
                          'evnt':  birth.health_id.upper(), \
                          'age': birth.humanised_age(), \
                          'mobile': chw.connection().identity }
            
            else:
                msg = _(u"%(child)s, %(gender)s %(age)s, in %(location)s " \
                          "EventId: %(evnt)s Notificationno: %(notno)s " \
                          "Place of Birth: %(place)s CHW no: %(mobile)s") % \
                         {'child': birth, \
                           'gender': birth.get_gender_display(), \
                          'notno': birth.notification_no, \
                          'evnt':  birth.health_id.upper(), \
                          'age': birth.humanised_age(), \
                          'place': birth.get_place_display(),\
                          'location': birth.location.name, \
                          'mobile': chw.connection().identity }


            msg=_("Birth Alert: ")+msg
            send_alert(chief.reporter, msg, name = "Birth Alert: ")

        if birth.notification_no:
            if chw.manager and chw.manager != chw:
                msg = _(u"%(rbirth)s, %(gender)s %(age)s, in %(location)s " \
                        "EventNumber: %(evnt)s CHW no: %(mobile)s") % \
                         {'rbirth': birth, \
                          'gender': birth.get_gender_display(), 
                          'evnt':  birth.health_id.upper(), \
                          'age': birth.humanised_age(), \
                          'location': birth.location.name, \
                          'mobile': chw.connection().identity }

                msg=_("Birth Alert! ")+msg
                send_alert(chw.manager.reporter, msg, name = "Birth Alert")  
    
        #PUSH TO OXD death object
        servelet(birth.pk)
