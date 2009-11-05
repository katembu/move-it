#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from django.utils.translation import ugettext as _

import rapidsms
from rapidsms.parsers.keyworder import Keyworder

from mctc.models.logs import MessageLog, log
from mctc.models.general import Case
from mctc.models.reports import Observation
from models import ReportMalaria

import re, datetime

def registered (func):
    def wrapper (self, message, *args):
        if message.persistant_connection.reporter:
            return func(self, message, *args)
        else:
            message.respond(_(u"Sorry, only registered users can access this program."))
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
        
    @keyword(r'mrdt \+(\d+) ([yn]) ([yn])?(.*)')
    @registered
    def report_malaria(self, message, ref_id, result, bednet, observed):
        case = self.find_case(ref_id)
        observed, choices = self.get_observations(observed)
        self.delete_similar(case.reportmalaria_set)
        reporter = message.persistant_connection.reporter

        result = result.lower() == "y"
        bednet = bednet.lower() == "y"

        report = ReportMalaria(case=case, reporter=reporter, result=result, bednet=bednet)
        report.save()
        for obs in observed:
            report.observed.add(obs)
        report.save()

        # build up an information dictionary
        info = case.get_dictionary()
        info.update(report.get_dictionary())
        info.update({
            "reporter_name": reporter.full_name(),
            "reporter_alias":reporter.alias,
            "reporter_identity":reporter.connection().identity,
        })

        # this could all really do with cleaning up
        # note that there is always an alert that goes out
        if not result:
            if observed: info["observed"] = ", (%s)" % info["observed"]
            msg = _("MRDT> Child +%(ref_id)s, %(last_name)s, %(first_name)s, "\
                    "%(gender)s/%(age)s (%(guardian)s), %(location)s. RDT=%(result_text)s,"\
                    " Bednet=%(bednet_text)s%(observed)s. Please refer patient IMMEDIATELY "\
                    "for clinical evaluation" % info)
            # alerts to health team
            alert = _("MRDT> Negative MRDT with Fever. +%(ref_id)s, %(last_name)s,"\
                      " %(first_name)s, %(gender)s/%(age)s %(location)s. Patient "\
                      "requires IMMEDIATE referral. Reported by CHW %(reporter_name)s "\
                      "@%(reporter_alias)s m:%(reporter_identity)s." % info)

        else:
            # this is all for if child has tested postive
            # and is really just abut
            years, months = case.years_months()
            tabs, yage = None, None
            # just reformatted to make it look like less ugh
            if years < 1:
                if months < 2: tabs, yage = None, None
                else: tabs, yage = 1, "less than 3"
            elif years < 3: tabs, yage = 1, "less than 3"
            elif years < 9: tabs, yage = 2, years
            elif years < 15: tabs, yage = 3, years
            else: tabs, yage = 4, years

            # messages change depending upon age and dangers
            dangers = report.observed.filter(uid__in=("vomiting", "appetite", "breathing", "confusion", "fits"))
            # no tabs means too young
            if not tabs:
                info["instructions"] = "Child is too young for treatment. Please refer IMMEDIATELY to clinic"
            else:
                # old enough to take tabs, but lets format msg
                if dangers:
                    info["danger"] = " and danger signs (" + ",".join([ u.name for u in dangers ]) + ")"                        
                    info["instructions"] = "Refer to clinic immediately after %s "\
                                           "tab%s of Coartem is given" % (tabs, (tabs > 1) and "s" or "")
                else:
                    info["danger"] = ""
                    info["instructions"] = "Child is %s. Please provide %s tab%s "\
                                           "of Coartem (ACT) twice a day for 3 days" % (yage, tabs, 
                                           (tabs > 1) and "s" or "")

            # finally build out the messages
            msg = _("MRDT> Child +%(ref_id)s, %(last_name)s, %(first_name)s, "\
                    "%(gender)s/%(age)s has MALARIA%(danger)s. %(instructions)s" % info)

            alert = _("MRDT> Child +%(ref_id)s, %(last_name)s, %(first_name)s, "\
                      "%(gender)s/%(months)s (%(location)s) has MALARIA%(danger)s. "\
                      "CHW: @%(reporter_alias)s %(reporter_identity)s" % info)

        if len(msg) > self.MAX_MSG_LEN:
            message.respond(msg[:self.MAX_MSG_LEN])
            message.respond(msg[self.MAX_MSG_LEN:])
        else:
            message.respond(msg)
        """ @todo: enable alerts """
        """
        recipients = report.get_alert_recipients()
        for recipient in recipients:
            message.forward(recipient.mobile, alert)
        """    

        log(case, "mrdt_taken")        
        return True
