#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
from django.db import models

import rapidsms
from rapidsms.parsers.keyworder import Keyworder
from django.utils.translation import ugettext_lazy as _

from mctc.models.logs import MessageLog
from mctc.models.general import Case
from mctc.models.reports import ReportCHWStatus
from reporters.models import Reporter, ReporterGroup
from models import ReportMeasles

import time

def registered (func):
    def wrapper (self, message, *args):
        if message.persistant_connection.reporter:
            return func(self, message, *args)
        else:
            message.respond(_(u"%s")%"Sorry, only registered users can access this program.")
            return True
    return wrapper

class HandlerFailed (Exception):
    pass

class App (rapidsms.app.App):
    MAX_MSG_LEN = 140
    keyword = Keyworder()
    handled = False
    def start (self):
        """Configure your app in the start phase."""
        pass

    def parse (self, message):
        message.was_handled = False

    def handle (self, message):
        try:
            func, captures = self.keyword.match(self, message.text)
        except TypeError:
            # didn't find a matching function
            # make sure we tell them that we got a problem
            #message.respond(_("Unknown or incorrectly formed command: %(msg)s... Please re-check your message") % {"msg":message.text[:10]})
            
            return False
        try:
            self.handled = func(self, message, *captures)
        except HandlerFailed, e:
            message.respond(e.message)
            
            self.handled = True
        except Exception, e:
            # TODO: log this exception
            # FIXME: also, put the contact number in the config
            message.respond(_("An error occurred. Please call 0733202270."))
            raise
        message.was_handled = bool(self.handled)
        return self.handled

    def cleanup (self, message):
        if bool(self.handled):
            log = MessageLog(mobile=message.peer,
                         sent_by=message.persistant_connection.reporter,
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

    @keyword(r'measles ?(.*)')
    @registered
    def measles(self, message, text):        
        reporter = message.persistant_connection.reporter
        cases, notcases = self.str_to_cases(text)
        result = ""
        for case in cases:
            result = result + "+%s "%case.ref_id
            report = ReportMeasles(case=case, reporter=reporter, taken=True)
            report.save()
        if result != "":
            msg = result + " received measles shot."
            message.respond(_("%s")%msg)
        if notcases:
            nresult = "" 
            for nc in notcases:
                nresult = nresult +"%s "%nc
            msg = nresult + " not found!!"            
            message.respond(_("%s")%msg)
        return True
    
    
    def str_to_cases(self, text): 
        '''
        @text a string containing space separeted +PID, e.g +78 +98 ..or 78 98 ...
        @return: Case Object list, and a list of numbers that were not cases
        '''       
        text = text.replace("+","")
        cs = text.split(" ")
        cases = []
        notcases = []
        for c in cs:
            try:
                cases.append(self.find_case(c))
            except HandlerFailed:
                notcases.append(c)
        return cases, notcases
    
    '''
    Send measles summary to health facilitators
    and those who are to receive alerts
    '''
    @keyword(r'msummary')
    def measles_summary(self, message):        
        header = u"Measles Summary by facility:"
        result = []
        
        summary =  ReportCHWStatus.measles_mini_summary()
        tmp = header
        for info in summary:
            if info["eligible_cases"] != 0:
                info["percentage"] = round(float(float(info["vaccinated_cases"])/float(info["eligible_cases"]))*100, 0)
            else:
                info["percentage"] = 0 
            item = u" %(clinic)s: %(vaccinated_cases)s/%(eligible_cases)s %(percentage)s,"%info
            if len(tmp) + len(item) + 2 >= self.MAX_MSG_LEN:
                result.append(tmp)
                tmp = header
            tmp += item
        if tmp != header:
            result.append(tmp)
        #message.forward(u"0733202270", u"Start Measles Summary...")
            
        subscribers = Reporter.objects.all()
        for text in result:
            for subscriber in subscribers:
                try:
                    if subscriber.registered_self and ReporterGroup.objects.get(title='measles_summary') in subscriber.groups.only():                
                        mobile = subscriber.connection().identity
                        message.forward(mobile, _("%s")%text)          
                except:
                    """
                    FIXME: The group might have not been created, need to alert the developer/in charge here
                    """
                    pass
                
        #message.forward(u"0733202270", u"...Measles Summary End")
        return True