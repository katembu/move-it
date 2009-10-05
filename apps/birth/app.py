#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import rapidsms
from rapidsms.parsers.keyworder import Keyworder

from django.db import transaction

from mctc.models.logs import MessageLog, log
from mctc.models.general import Provider, Case
from birth.models import ReportBirth

import re
import time, datetime

def _(txt): return txt

def authenticated (func):
    def wrapper (self, message, *args):
        if message.sender:
            return func(self, message, *args)
        else:
            message.respond(_("%s is not a registered number.")
                            % message.peer)
            return True
    return wrapper

class HandlerFailed (Exception):
    pass

class App (rapidsms.app.App):
    MAX_MSG_LEN = 140
    keyword = Keyworder()
    def start (self):
        """Configure your app in the start phase."""
        pass

    def parse (self, message):
        # allow authentication to occur when http tester is used
        if message.peer[:3] == '254':
            mobile = "+" + message.peer
        else:
            mobile = message.peer 
        provider = Provider.by_mobile(mobile)
        if provider:
            message.sender = provider.user
        else:
            message.sender = None
        message.was_handled = False

    def handle (self, message):
        try:
            func, captures = self.keyword.match(self, message.text)
        except TypeError:
            # didn't find a matching function
            # make sure we tell them that we got a problem
            message.respond(_("Unknown or incorrectly formed command: %(msg)s... Please re-check your message") % {"msg":message.text[:10]})
            
            return False
        try:
            handled = func(self, message, *captures)
        except HandlerFailed, e:
            message.respond(e.message)
            
            handled = True
        except Exception, e:
            # TODO: log this exception
            # FIXME: also, put the contact number in the config
            message.respond(_("An error occurred. Please call 0733202270."))
            raise
        message.was_handled = bool(handled)
        return handled

    def cleanup (self, message):
        log = MessageLog(mobile=message.peer,
                         sent_by=message.sender,
                         text=message.text,
                         was_handled=message.was_handled)
        log.save()

    def outgoing (self, message):
        """Handle outgoing message notifications."""
        pass

    def stop (self):
        """Perform global app cleanup when the application is stopped."""
        pass
    
    @keyword("birth (\S+) (\S+) ([MF]) (\d+) ([0-9]*\.[0-9]+|[0-9]+) ([A-Z]) (\S+)?(.+)*")
    @authenticated
    @transaction.commit_on_success
    def report_birth(self, message, last, first, gender, dob, weight,location, guardian, complications=""):
        if len(dob) != 6:
            # There have been cases where a date like 30903 have been sent and
            # when saved it gives some date that is way off
            raise HandlerFailed(_("Date must be in the format ddmmyy: %s") % dob)
        else:
            dob = re.sub(r'\D', '', dob)
            try:
                dob = time.strptime(dob, "%d%m%y")
            except ValueError:
                try:
                    dob = time.strptime(dob, "%d%m%Y")
                except ValueError:
                    raise HandlerFailed(_("Couldn't understand date: %s") % dob)
            dob = datetime.date(*dob[:3])        
        provider = message.sender.provider
        zone = None
        if not zone:
            if provider.clinic:
                zone = provider.clinic.zone
        
        info = {
            "first_name" : first.title(),
            "last_name"  : last.title(),
            "gender"     : gender.upper(),
            "dob"        : dob,
            "guardian"   : guardian.title(),
            "mobile"     : "",
            "provider"   : provider,
            "zone"       : zone
        }
        
        abirth = ReportBirth(location=location.upper())
        #Perform Location checks
        if abirth.get_location() is None:
            raise HandlerFailed(_("Location `%s` is not known. Please try again with a known location") % location)
        
        iscase = Case.objects.filter(first_name=info['first_name'], last_name=info['last_name'], provider=info['provider'], dob=info['dob'])
        if iscase:
            info["PID"] = iscase[0].ref_id
            self.info(iscase[0].id)
            self.info(info)
            #message.respond(_(
            #"%(last_name)s, %(first_name)s (+%(PID)s) has already been registered by %(provider)s.") % info)
            # TODO: log this message
            case = iscase[0]
        else:
            case = Case(**info)
            case.save()
            log(case, "patient_created")
        
        info.update({
            "id": case.ref_id,
            "last_name": last.upper(),
            "age": case.age(),
            "dob": dob.strftime("%d/%m/%y")
        })
        
        info2 = {
            "case":case,
            "weight": weight,
            "location": location,
            "provider": provider,
            "complications": complications
        }
        
        #check if birth has already been reported
        rbirth = ReportBirth.objects.filter(case=case)
        
        if rbirth:
            raise HandlerFailed(_(
            "The birth of %(last_name)s, %(first_name)s (+%(PID)s) has already been reported by %(provider)s.") % info)
            
        
        abirth = ReportBirth(**info2)
        abirth.save()
        
        if zone:
            info["zone"] = zone.name
        message.respond(_(
            "Birth +%(id)s: %(last_name)s, %(first_name)s %(gender)s/%(dob)s " +
            "(%(guardian)s) %(zone)s") % info)
        
        
        return True