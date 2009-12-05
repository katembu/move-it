#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from django.utils.translation import ugettext as _

import rapidsms
from rapidsms.parsers.keyworder import Keyworder

from childcount.models.logs import MessageLog, log
from childcount.models.general import Case
from childcount.models.reports import Observation
from models import ReportMalaria

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
        '''Configure your app in the start phase.'''
        pass

    def parse (self, message):
        message.was_handled = False

    def handle (self, message):
        try:
            func, captures = self.keyword.match(self, message.text)
        except TypeError:
            #If the command included 'mrdt', respond by reminding the user of the correct format for the command           
            mrdt_input = message.text.lower()
            if not (mrdt_input.find("mts") == -1):
                message.respond(self.get_mrdt_format_reminder())
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
        
    @keyword(r'mtk (\d+).*')
    def give_treatmet_reminder(self, message, kg):
        weight = int(kg)        
        dosage = ""
        if weight > 5: dosage = "one quarter"
        if weight > 10: dosage = "one half"
        if weight > 24: dosage = "one"
        if weight > 50: dosage = "one and a half"
        if weight > 70: dosage = "two"
        
        if weight < 5:
            message.respond(_("Child is too light for treatment (under 5kg).  Refer to clinic."))     
            return True     
        reminder = _("Patient is %skg.  If positive for malaria, take %s each of Artesunate (50mg) and Amodiaquine (150mg) morning and evening for 3 days." % (weight, dosage))
        message.respond(reminder)
        return True

    def get_mrdt_format_reminder(self):
        '''Expected format for mrdt input, sent as a reminder'''
        return "Format:  mts +[patient_ID\] malaria[+/-] bednet[y/n] symptoms separated by spaces[D CG A F V NR UF B CV CF]"

    @keyword(r'^mts\s*\+?(\d+)\s*([a-zA-z+-])\s*(\S)\s*(.*)$')
    @registered
    def report_malaria(self, message, ref_id, result, bednet, observed):
        '''Processes incoming mrdt reports.  Expected format is as above.  Can process inputs without spaces, but symptoms must have spaces between them.  '+' and 'y' register as positive for malaria, all other characters register as negative. 'y' registers as yes for a bednet, all other characters register as no.'''
        
       
        case = self.find_case(ref_id)
        observed, choices = self.get_observations(observed)
        self.delete_similar(case.reportmalaria_set)
        reporter = message.persistant_connection.reporter

        result = (result == "+" or result.lower() == "y")
        bednet = (bednet.lower() == "y")

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
                if months < 5: tabs, yage = None, None
                else: tabs, yage = "one quarter", "under one year (5-10kg)"
            elif years < 7: tabs, yage = "one half", "1-6 years (11-24kg)"
            elif years < 14: tabs, yage = "one ", "7-13 years (25-50kg)"
            elif years < 18: tabs, yage = "one and a half", "14 - 17 years (50-70kg)"
            else: tabs, yage = "two", "18+ years (70+ kg)"

            # messages change depending upon age and dangers
            dangers = report.observed.filter(uid__in=("vomiting", "appetite", "breathing", "confusion", "fits"))
            # no tabs means too young
            if not tabs:
                info["instructions"] = "Child is too young for treatment. Please refer IMMEDIATELY to clinic"
            else:
                # old enough to take tabs, but lets format msg
                if dangers:
                    info["danger"] = " and danger signs (" + ",".join([ u.name for u in dangers ]) + ")"                        
                    info["instructions"] = "Refer to clinic after %s "\
                                           " each of Artesunate 50mg and Amodiaquine 150mg is given" % (tabs)
                else:
                    info["danger"] = ""
                    info["instructions"] = "Child is %s. %s each of Artesunate 50mg and Amodiaquine 150mg morning and evening for 3 days" % (yage, tabs)

            # finally build out the messages
            msg = _("Patient +%(ref_id)s, %(first_name)s %(last_name)s, %(gender)s/%(age)s (%(guardian)s). Bednet=%(bednet_text)s %(observed)s.  Patient has MALARIA%(danger)s." % (info))

            alert = _("MRDT> Child +%(ref_id)s, %(last_name)s, %(first_name)s, "\
                      "%(gender)s/%(months)s (%(location)s) has MALARIA%(danger)s. "\
                      "CHW: @%(reporter_alias)s %(reporter_identity)s" % info)

        message.respond(msg)
        message.respond(_(info["instructions"]))
        ''' @todo: enable alerts '''
        '''
        recipients = report.get_alert_recipients()
        for recipient in recipients:
            message.forward(recipient.mobile, alert)
        '''    

        log(case, "mrdt_taken")       
        return True 

    def get_mrdt_report_format_reminder(self):
        '''Expected format for mrdt command, sent as a reminder'''
        return "Format:  mrdt +[patient_ID\] malaria[y/n] bednet[y/n] symptoms separated by spaces[D CG A F V NR UF B CV CF]"

    @keyword(r'mrdt \+(\d+) ([yn]) ([yn])?(.*)')
    @registered
    def report_malaria(self, message, ref_id, result, bednet, observed):
        case = self.find_case(ref_id)
        observed, choices = self.get_observations(observed)
        self.delete_similar(case.reportmalaria_set)
        reporter = message.persistant_connection.reporter
        self.log("debug", bednet)
        result = result.lower() == "y"
        bednet = bednet.lower() == "y"
        alert = None

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
            if observed: 
                info["observed"] = ", (%s)" % info["observed"]
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
                msg = _("MRDT> Child +%(ref_id)s, %(last_name)s, %(first_name)s, "\
                        "%(gender)s/%(age)s (%(guardian)s), %(location)s. RDT=%(result_text)s,"\
                        " Bednet=%(bednet_text)s." % info)

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
            '''
            FIXME: Either make this an intelligent breakup of the message or let the backend handle that.
            '''
            message.respond(msg[:msg.rfind(". ")+1])            
            message.respond(msg[msg.rfind(". ")+1:])
        else:
            message.respond(msg)
        
        if alert:
            recipients = report.get_alert_recipients()
            for recipient in recipients:
                if len(alert) > self.MAX_MSG_LEN:
                    message.forward(recipient.connection().identity, alert[:alert.rfind(". ")+1])            
                    message.forward(recipient.connection().identity, alert[alert.rfind(". ")+1:])
                else:
                    message.forward(recipient.connection().identity, alert)
            

        log(case, "mrdt_taken")        
        return True

