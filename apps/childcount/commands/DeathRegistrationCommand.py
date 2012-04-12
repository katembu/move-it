#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: katembu

import re, random
from datetime import date, datetime

from django.db import models
from django.db.models import Q

from django.utils.translation import ugettext as _

from locations.models import Location

from childcount.utils import clean_names, DOBProcessor, random_id
from childcount.utils import send_msg, send_alert, authenticated, servelet

from childcount.models import Configuration
from childcount.models import Patient, CHW as CHWES

from childcount.exceptions import BadValue, ParseError

from childcount.forms.utils import MultipleChoiceField
from childcount.commands import CCCommand


class DeathRegistrationCommand(CCCommand):
    """ Register a new deaths
    Params:
        * location
        * names
        * gender
        * age or DOB
        * dod
        * Place
        * Notification Number
        * Mobile
    """

    KEYWORDS = {
        'en': ['death', 'dea', 'death!'],
    }

    OVERIDE_KEYWORDS = ['death!']

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
        death = Patient()
        death.chw = chw

        #Check if CHW has permission i.e Chief, Assistant Chief
        
        allowed_groups = ("Assistant Chief", "CHW", "Chief")
        reporters = CHWES.objects.filter(\
                                user_ptr__groups__name__in=allowed_groups)

        if chw not in reporters:
            raise ParseError(_(u"Youre not allowed to report Events "))


        expected = _(u"location | dead person names | gender | age or " \
                      "DOB | dat eof death | place | mobile")
        if len(self.params) < 8:
            raise ParseError(_(u"Not enough information. Expected: " \
                                "%(keyword)s %(expected)s") % \
                                {'keyword': self.params[0], \
                                'expected': expected})


        #event id
        death.health_id = random_id()

        #Event Type
        death.event_type = Patient.DEATH

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

        death.location = location

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
                death.dob = dob

                days, weeks, months = death.age_in_days_weeks_months(\
                    self.date.date())
                if days < 60 and variance > 1:
                    raise BadValue(_(u"You must provide an exact birth date " \
                                      "for children under 2 months."))
                elif months < 24 and variance > 30:
                    raise BadValue(_(u"You must provide an exact birth date " \
                                      "or the age, in months, for children " \
                                      "under two years."))
                elif death.dob > date.today():
                    raise BadValue(_("The birth date you gave %(bdate)s) " \
                                     "is in the future!  Please try " \
                                     "reentering the date with the full " \
                                     "year (like 2009 instead of 09).") % \
                                     {'bdate': death.dob.strftime('%d-%b-%Y')})

        if not dob:
            raise ParseError(_(u"Could not understand age or " \
                                    "date_of_birth of %(string)s.") % \
                                    {'string': tokens[i + 1]})

        death.estimated_dob = variance > 1

        # if the gender field is the first or second
        if i == 0:
            raise ParseError(_(u"You must provide a death name before " \
                                "their sex."))

        death.last_name, death.first_name, alias = \
                             clean_names(' '.join(tokens[:i]), \
                             surname_first=self.SURNAME_FIRST)

        # remove the name tokens
        tokens = tokens[i:]

        # remove the gender token
        death.gender = self.gender_field.get_db_value(tokens.pop(0))

        # remove the dob token
        tokens.pop(0)

        if len(tokens) == 0:
            raise ParseError(_(u"You must provide the date of death"))
        if len(tokens[0]) < 4:
            raise ParseError(_(u"Could not understand date_of_death of "\
                                "%(string)s. Please provide an exact date of"\
                                " death in the format DDMMYY.") % \
                                    {'string': tokens[0]})
        try:
            dod, variance = DOBProcessor.from_dob(lang, tokens[0], \
                                                  self.date.date())
        except:
            raise ParseError(_(u"Could not understand date_of_death of "\
                                "%(string)s. Please provide an exact date of"\
                                " death in the format DDMMYY.") % \
                                {'string': tokens[0]})

        if dod:
            death.dod = dod

            if death.dod > date.today():
                raise BadValue(_("The Death date you gave %(ddate)s) " \
                              "is in the future!  Please try reentering " \
                              "the date with the full year ") % \
                              {'ddate': death.dod.strftime('%d-%b-%Y')})
            elif death.dob > death.dod:
                raise BadValue(_("The Death date you gave (%(ddate)s) " \
                              "is less than Birth Date (%(bdate)s) ! Please "\
                              "try reentering the date with the full year") % \
                              {'ddate': death.dod.strftime('%d-%b-%Y'),
                               'bdate': death.dob.strftime('%d-%b-%Y')})

        if not dod:
            raise ParseError(_(u"Could not understand " \
                                "date_of_death of %(string)s.") % \
                                {'string': tokens[0]})
    
        #remove the dod token
        tokens.pop(0)

        '''
        Place the death occured
        If place of death is hospital expect notification number or (U) Unknown
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
                                "death with a %(choices)s.") % \
                              {'choices': self.place_field.choices_string()})

        #Remove the place token
        death.place = self.place_field.get_db_value(tokens.pop(0))
        
        #notification number
        if death.place == Patient.HEALTH_FACILITY:
            if(len(tokens) < 2):
                raise ParseError(_(u"You must indicate notification number  " \
                               "if place is clinic or U for notissued/Unkown"))
            #Notification number
            noti_number = ''.join(tokens[0])
            #noti_number = re.sub('\D', '', noti_number)
            if len(noti_number) > 10:
                raise BadValue(_(u"Notification number cannot be longer "\
                                  "than 10 digits."))
            if noti_number.upper() != Patient.CERT_UNVERIFIED:
                death.notification_no = noti_number
                death.cert_status = Patient.CERT_VERIFIED        
                
            #Remove the notification token
            tokens.pop(0)
   
        #Mobile number
        mobile = ''.join(tokens[0:])
        mobile = re.sub('\D', '', mobile)
        if not mobile.isdigit():
            raise BadValue(_(u"Expected: phone number."))

        if len(mobile) < 10:
            raise BadValue(_(u"Phone number is too short"))
        if len(mobile) > 10:
            raise BadValue(_(u"Check mobile number format. Its too long"))

        death.mobile = mobile

        #Counter check if death exist
        death_check = Patient.objects.filter( \
                                first_name__iexact=death.first_name, \
                                last_name__iexact=death.last_name, \
                                dob=death.dob,  dod=death.dod, \
                                event_type = Patient.DEATH )

        if len(death_check) > 0:
            old_p = death_check[0]
            if old_p.chw == chw:
                death_chw = _(u"you")
            else:
                death_chw = death_check[0].chw
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
                               'chw': death_chw, \
                               'id': old_p.health_id.upper()})
        death.save()

        self.message.respond(_("You successfuly reported the death of" \
                                " %(death)s, %(gender)s %(age)s in %(loc)s "\
                                 "and EventId is: %(evnt)s ") %  
                                    {'death': death, \
                                     'gender': death.get_gender_display(), \
                                      'evnt': death.health_id.upper(), \
                                      'loc': death.location.name, \
                                      'age': death.humanised_age()})



        #Send alert to chief (Chief can be CHW )
        groups = ("Assistant Chief", "Chief")
        chief = False
        try:
            chief = CHWES.objects.exclude(pk=chw.pk).filter( \
                                        user_ptr__groups__name__in=groups, \
                                         assigned_location=death.location)[0]

            #chief =  chief.filter(~Q(pk=chw.pk))[0]
        except IndexError:
            print "CHIEF DOESNOT EXIST "
            pass

        if chief and chief != chw:
            if death.notification_no == Patient.CERT_UNVERIFIED:
                msg = _(u"%(child)s, %(gender)s %(age)s, in %(location)s " \
                            "EventId: %(evnt)s CHW no" \
                            ":%(mobile)s") % \
                         {'child': death, \
                          'gender': death.get_gender_display(), \
                          'location': death.location.name, \
                          'evnt':  death.health_id.upper(), \
                          'age': death.humanised_age(), \
                          'mobile': chw.connection().identity }
            
            else:
                msg = _(u"%(child)s, %(gender)s %(age)s, in %(location)s " \
                          "EventId: %(evnt)s Notificationno: %(notno)s " \
                          "Place of Death: %(place)s CHW no: %(mobile)s") % \
                         {'child': death, \
                           'gender': death.get_gender_display(), \
                          'notno': death.notification_no, \
                          'evnt':  death.health_id.upper(), \
                          'age': death.humanised_age(), \
                          'place': death.get_place_display(),\
                          'location': death.location.name, \
                          'mobile': chw.connection().identity }

            msg=_("Death Alert! ")+msg
            send_alert(chief.reporter, msg, name = "Death Alert")

        #The CHW manager should recived verified Death only
        #Send alert to Managers and not self
        if death.notification_no:
            if chw.manager and chw.manager != chw:
                msg = _(u"%(rdeath)s, %(gender)s %(age)s, in %(location)s " \
                        "EventNumber: %(evnt)s CHW no: %(mobile)s") % \
                         {'rdeath': death, \
                          'gender': death.get_gender_display(), 
                          'evnt':  death.health_id.upper(), \
                          'age': death.humanised_age(), \
                          'location': death.location.name, \
                          'mobile': chw.connection().identity }

                msg=_("Death Alert! ")+msg
                send_alert(chw.manager.reporter, msg, name = "Death Alert")
                

        #PUSH TO OXD death object
        servelet(death.pk)
