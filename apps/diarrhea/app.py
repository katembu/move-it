#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import rapidsms
from rapidsms.parsers.keyworder import Keyworder

from django.db import models
from django.utils.translation import ugettext as _

from childcount.models.logs import MessageLog, log
from childcount.models.general import Case
from models import ReportDiarrhea, DiarrheaObservation

import re, datetime

find_diagnostic_re = re.compile('( -[\d\.]+)',re.I)
find_lab_re =  re.compile('(/[A-Z]+)([\+-])(\d*:?)', re.I)


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
        '''Configure your app in the start phase.'''
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
        '''Handle outgoing message notifications.'''
        pass

    def stop (self):
        '''Perform global app cleanup when the application is stopped.'''
        pass

    def find_case (self, ref_id):
        try:
            return Case.objects.get(ref_id=int(ref_id))
        except Case.DoesNotExist:
            raise HandlerFailed(_("Case +%s not found.") % ref_id)

    # DIARRHEA
    # follow up on diarrhea
    @keyword(r'ors \+(\d+) ([yn])')
    @registered
    def followup_diarrhea(self, message, ref_id, is_ok):
        case    = self.find_case(ref_id)
        is_ok   = True if is_ok == "y" else False

        reporter = message.persistant_connection.reporter
        report = ReportDiarrhea.objects.get(case=case)
        
        if is_ok:
            report.status   = ReportDiarrhea.HEALTHY_STATUS
            report.save()
        else:
            report.status   = ReportDiarrhea.SEVERE_STATUS
            report.save()

            info = report.case.get_dictionary()
            info.update(report.get_dictionary())
   
            msg = _("%(diagnosis_msg)s. +%(ref_id)s %(last_name)s, %(first_name_short)s, %(gender)s/%(months)s (%(guardian)s). %(days)s, %(ors)s") % info
            if report.observed.all().count() > 0: msg += ", " + info["observed"]
            
            message.respond("DIARRHEA> " + msg)
            
        
        '''
        if report.status in (report.MODERATE_STATUS,
                           report.SEVERE_STATUS,
                           report.DANGER_STATUS):
            alert = _("@%(username)s reports %(msg)s") % {"username":reporter.alias, "msg":msg}
            recipients = [reporter]
            for query in (Provider.objects.filter(alerts=True),
                          Provider.objects.filter(clinic=provider.clinic)):
                for recipient in query:
                    if recipient in recipients: continue
                    recipients.append(recipient)
                    message.forward(recipient.mobile, alert)
        '''      
        log(case, "diarrhea_fu_taken")
        return True
    
    def get_diarrheaobservations(self, text):
        choices  = dict([(o.letter, o) for o in DiarrheaObservation.objects.all()])
        observed = []
        if text:
            text = re.sub(r'\W+', ' ', text).lower()
            for observation in text.split(' '):
                obj = choices.get(observation, None)
                if not obj:
                    if observation != 'n':
                        raise HandlerFailed("Unknown observation code: %s" % observation)
                else:
                    observed.append(obj)
        return observed, choices

    @keyword(r'ors \+(\d+) ([yn]) (\d+)\s?([a-z\s]*)')
    @registered
    def report_diarrhea(self, message, ref_id, ors, days, complications):
        case = self.find_case(ref_id)

        ors     = True if ors == "y" else False
        days    = int(days)

        observed, choices = self.get_diarrheaobservations(complications)
        self.delete_similar(case.reportdiarrhea_set)

        reporter = message.persistant_connection.reporter
        report = ReportDiarrhea(case=case, reporter=reporter, ors=ors, days=days)
        report.save()
        for obs in observed:
            report.observed.add(obs)
        report.diagnose()
        report.save()

        choice_term = dict(choices)

        info = case.get_dictionary()
        info.update(report.get_dictionary())

        msg = _("%(diagnosis_msg)s. +%(ref_id)s %(last_name)s, %(first_name_short)s, %(gender)s/%(months)s (%(guardian)s). %(days)s, %(ors)s") % info

        if observed: msg += ", " + info["observed"]

        message.respond("DIARRHEA> " + msg)
        
        '''
        if report.status in (report.MODERATE_STATUS,
                           report.SEVERE_STATUS,
                           report.DANGER_STATUS):
            alert = _("@%(username)s reports %(msg)s") % {"username":provider.user.username, "msg":msg}
            recipients = [provider]
            for query in (Provider.objects.filter(alerts=True),
                          Provider.objects.filter(clinic=provider.clinic)):
                for recipient in query:
                    if recipient in recipients: continue
                    recipients.append(recipient)
                    message.forward(recipient.mobile, alert)
        '''
        log(case, "diarrhea_taken")
        return True            

    def delete_similar(self, queryset):
        try:
            last_report = queryset.latest("entered_at")
            if (datetime.datetime.now() - last_report.entered_at).days == 0:
                # last report was today. so delete it before filing another.
                last_report.delete()
        except models.ObjectDoesNotExist:
            pass
