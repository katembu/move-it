#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
from django.db import models
from django.utils.translation import ugettext as _

import rapidsms
from rapidsms.parsers.keyworder import Keyworder

from mctc.models.logs import MessageLog, log
from mctc.models.general import Case
from models import ReportMalnutrition, Observation

import re, datetime

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
            input_text = message.text.lower()
            if not (input_text.find("muac") == -1):
                message.respond(self.get_muac_report_format_reminder())
                self.handled = True
                return True
            return False
        try:
            self.handled = func(self, message, *captures)
        except HandlerFailed, e:
            message.respond(e.message)
            
            self.handled = True
        except Exception, e:
            # TODO: log this exception
            # FIXME: also, put the contact number in the config
            message.respond(_("%s")%"An error occurred. Please call 0733202270.")
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
        
    def get_observations(self, text):
        choices  = dict( [ (o.letter, o) for o in Observation.objects.all() ] )
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
    
    def delete_similar(self, queryset):
        try:
            last_report = queryset.latest("entered_at")
            if (datetime.datetime.now() - last_report.entered_at).days == 0:
                # last report was today. so delete it before filing another.
                last_report.delete()
        except models.ObjectDoesNotExist:
            pass
        
    def get_muac_report_format_reminder(self):
        """Expected format for muac command, sent as a reminder"""
        return "Format:  muac +[patient_ID\] muac[measurement] edema[e/n] symptoms separated by spaces[CG D A F V NR UF]"        
    
    #change location    
    
    keyword.prefix = ["muac", "pb"]
    @keyword(r'\+(\d+) ([\d\.]+)( [\d\.]+)?( [\d\.]+)?( (?:[a-z]\s*)+)')
    @registered
    def report_case (self, message, ref_id, muac,
                     weight, height, complications):
        case = self.find_case(ref_id)
        try:
            muac = float(muac)
            if muac < 30: # muac is in cm?
                muac *= 10
            muac = int(muac)
        except ValueError:
            raise HandlerFailed(
                _("Can't understand MUAC (mm): %s") % muac)

        if weight is not None:
            try:
                weight = float(weight)
                if weight > 100: # weight is in g?
                    weight /= 1000.0
            except ValueError:
                raise HandlerFailed("Can't understand weight (kg): %s" % weight)

        if height is not None:
            try:
                height = float(height)
                if height < 3: # weight height in m?
                    height *= 100
                height = int(height)
            except ValueError:
                raise HandlerFailed("Can't understand height (cm): %s" % height)

        observed, choices = self.get_observations(complications)
        self.delete_similar(case.reportmalnutrition_set)

        reporter = message.persistant_connection.reporter
        report = ReportMalnutrition(case=case, reporter=reporter, muac=muac,
                        weight=weight, height=height)
        report.save()
        for obs in observed:
            report.observed.add(obs)
        report.diagnose()
        report.save()

        #choice_term = dict(choices)

        info = case.get_dictionary()
        info.update(report.get_dictionary())

        msg = _("%(diagnosis_msg)s. +%(ref_id)s %(last_name)s, %(first_name_short)s, %(gender)s/%(months)s (%(guardian)s). MUAC %(muac)s") % info

        if weight: msg += ", %.1f kg" % weight
        if height: msg += ", %.1d cm" % height
        if observed: msg += ", " + info["observed"]

        message.respond("MUAC> " + msg)
        
        
        if report.status in (report.MODERATE_STATUS,
                           report.SEVERE_STATUS,
                           report.SEVERE_COMP_STATUS):
            alert = _("@%(username)s reports %(msg)s") % {"username":report.reporter.alias, "msg":msg}
            
            recipients = report.get_alert_recipients()
            for recipient in recipients:
                if len(alert) > self.MAX_MSG_LEN:
                    message.forward(recipient.connection().identity, alert[:alert.rfind(". ")+1])            
                    message.forward(recipient.connection().identity, alert[alert.rfind(". ")+1:])
                else:
                    message.forward(recipient.connection().identity, alert)
        
        log(case, "muac_taken")
        return True
