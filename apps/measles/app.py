#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
from django.db import models

import rapidsms
from rapidsms.parsers.keyworder import Keyworder

from mctc.models.logs import MessageLog
from mctc.models.general import Provider, Case
from mctc.models.reports import ReportCHWStatus
from mctc.models.measles import ReportMeasles

import time

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

    @keyword(r'measles ?(.*)')
    @authenticated
    def measles(self, message, text):        
        provider = message.sender.provider
        cases, notcases = self.str_to_cases(text)
        result = ""
        for case in cases:
            result = result + "+%s "%case.ref_id
            report = ReportMeasles(case=case, provider=provider, taken=True)
            report.save()
        message.respond(_(result + " received measles shot."))
        if notcases:
            nresult = "" 
            for nc in notcases:
                nresult = nresult +"%s "%nc            
            message.respond(_(nresult + " not found!!"))
        return True
    
    '''
        @text a string containing space separeted +PID, e.g +78 +98 ..or 78 98 ...
        @return: Case Object list, and a list of numbers that were not cases
    '''
    def str_to_cases(self, text):        
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
        summary =  ReportCHWStatus.measles_mini_summary()
        header = u"Measles Summary by facility:"
        result = []
        tmp = header;
        for info in summary:
            info["percentage"] = round(float(float(info["vaccinated_cases"])/float(info["eligible_cases"]))*100, 0); 
            item = u" %(clinic)s: %(vaccinated_cases)s/%(eligible_cases)s %(percentage)s,"%info
            if len(tmp) + len(item) + 2 >= self.MAX_MSG_LEN:
                result.append(tmp)
                tmp = header
            tmp += item
        if tmp != header:
            result.append(tmp)
        message.forward(u"0733202270", u"Start...")    
        time.sleep(10)
        providers = Provider.objects.filter(alerts=True).order_by("mobile").reverse()
        for text in result:
            for provider in providers:
                mobile = u"0" + provider.mobile[4:]
                message.forward(mobile, text)
                time.sleep(10)
            message.forward(u"0733858137", text)
        message.forward(u"0733202270", u"...End")
        return True