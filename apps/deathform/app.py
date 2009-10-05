#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import rapidsms
from rapidsms.parsers.keyworder import Keyworder

from mctc.models.logs import MessageLog
from mctc.models.general import Provider, Case
from deathform.models.general import ReportDeath

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
    
    def find_case (self, ref_id):
        try:
            return Case.objects.get(ref_id=int(ref_id))
        except Case.DoesNotExist:
            raise HandlerFailed(_("Case +%s not found.") % ref_id)
    
    @keyword("death (\S+) (\S+) ([MF]) (\d+[YM]) (\d+) ([A-Z]) ([A-Z])?(.+)*")
    @authenticated
    def report_death(self, message, last, first, gender, age, dod, cause, location, description=""):
        
        if age[len(age)-1].upper() == 'Y':
            age = int(age[:len(age)-1])*12
        else:
            age = int(age[:len(age)-1])
        
        if len(dod) != 6:
            # There have been cases where a date like 30903 have been sent and
            # when saved it gives some date that is way off
            raise HandlerFailed(_("Date must be in the format ddmmyy: %s") % dod)
        else:
            dod = re.sub(r'\D', '', dod)
            try:
                dod = time.strptime(dod, "%d%m%y")
            except ValueError:
                try:
                    dod = time.strptime(dod, "%d%m%Y")
                except ValueError:
                    raise HandlerFailed(_("Couldn't understand date: %s") % dod)
            dod = datetime.date(*dod[:3])        
        provider = message.sender.provider
        death = ReportDeath(last_name=last,first_name=first,gender=gender.upper(),
                            age=age, provider=provider, location=location.upper(),cause=cause.upper(),
                            description=description, dod=dod)
        #Perform Location checks
        if death.get_location() is None:
            raise HandlerFailed(_("Location `%s` is not known. Please try again with a known location") % location)
        #Perform Cause Check  
        if death.get_cause() is None:
            raise HandlerFailed(_("Cause `%s` is not known. Please try again with a known death cause") % cause)
        
        death.save()
        info = death.get_dictionary()
        message.respond(_("%(name)s [%(age)s] died on %(dod)s of %(cause)s at %(location)s")%info)
        return True
    
    @keyword("cdeath \+(\d+) (\d+) ([A-Z]) ([A-Z])?(.+)*")
    @authenticated
    def report_cdeath(self, message, ref_id, dod, cause, location, description=""):
        #Is the child registered with us?
        case = self.find_case(ref_id)
        age = case.age()
        if age[len(age)-1].upper() == 'Y':
            age = int(age[:len(age)-1])*12
        else:
            age = int(age[:len(age)-1])
            
                
        if len(dod) != 6:
            # There have been cases where a date like 30903 have been sent and
            # when saved it gives some date that is way off
            raise HandlerFailed(_("Date must be in the format ddmmyy: %s") % dod)
        else:
            dod = re.sub(r'\D', '', dod)
            try:
                dod = time.strptime(dod, "%d%m%y")
            except ValueError:
                try:
                    dod = time.strptime(dod, "%d%m%Y")
                except ValueError:
                    raise HandlerFailed(_("Couldn't understand date: %s") % dod)
            dod = datetime.date(*dod[:3])        
        provider = message.sender.provider
        death = ReportDeath(last_name=case.last_name.upper(),first_name=case.first_name.upper(),gender=case.gender.upper(),
                            age=age, provider=provider, location=location.upper(),cause=cause.upper(),
                            description=description, dod=dod, case=case)
        #Perform Location checks
        if death.get_location() is None:
            raise HandlerFailed(_("Location `%s` is not known. Please try again with a known location") % location)
        #Perform Cause Check  
        if death.get_cause() is None:
            raise HandlerFailed(_("Cause `%s` is not known. Please try again with a known death cause") % cause)
        
        death.save()
        case.set_status(Case.STATUS_DEAD);
        case.save()
        info = death.get_dictionary()
        message.respond(_("%(name)s [%(age)s] died on %(dod)s of %(cause)s at %(location)s")%info)
        return True