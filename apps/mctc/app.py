#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.db import models
from django.utils.translation import ugettext as _

from reporters.models import Role, ReporterGroup, Reporter, PersistantConnection
from locations.models import Location, LocationType, RecursiveManager

#def _(txt): return txt

from django.contrib.auth.models import User, Group

import rapidsms
from rapidsms.parsers.keyworder import Keyworder
from rapidsms.message import Message
from rapidsms.connection import Connection

from models.logs import MessageLog, log, elog

from models.general import Provider, User
from models.general import Facility, Case, CaseNote, Zone

from models.reports import  Observation, DiarrheaObservation, ReportDiarrhea
from models.reports import ReportDiagnosis, Diagnosis, Lab, LabDiagnosis

import re, time, datetime

find_diagnostic_re = re.compile('( -[\d\.]+)' ,re.I)
find_lab_re =  re.compile('(/[A-Z]+)([\+-])(\d*:?)', re.I)

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

def registered (func):
    def wrapper (self, message, *args):
        if message.persistant_connection.reporter:
            return func(self, message, *args)
        else:
            message.respond(_(u"Sorry, only registered users can access this program."))
            return True
    return wrapper

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

    def cleanup (self, message):
        log = MessageLog(mobile=message.peer,
                         sent_by=message.sender,
                         text=message.text,
                         was_handled=message.was_handled)
        log.save()

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
            
            elog(message.sender, message.text)
            raise
        message.was_handled = bool(handled)
        return handled

    @keyword("join (\S+) (\S+) (\S+)(?: ([a-z]\w+))?")
    def join (self, message, clinic_code, last_name, first_name, username=None):
        ''' register a user and join the system '''

        # skip roles for now
        role_code   = None
        try:
            name = "%s %s"%(first_name, last_name)
            # parse the name, and create a reporter            
            alias, fn, ln = Reporter.parse_name(name)

            if not message.persistant_connection.reporter:
                rep = Reporter(alias=alias, first_name=fn, last_name=ln)
            else:
                rep = message.persistant_connection.reporter
                rep.alias       = alias
                rep.first_name  = fn
                rep.last_name   = ln

            rep.save()
            
            # attach the reporter to the current connection
            message.persistant_connection.reporter = rep
            message.persistant_connection.save()
                  
            # something went wrong - at the
            # moment, we don't care what
        except:
            message.respond("Join Error. Unable to register your account.")
            
        if role_code == None or role_code.__len__() < 1:
            role_code   = 'chw'

        reporter    = message.persistant_connection.reporter
        
        # check clinic code
        try:
            clinic  = Location.objects.get(code=clinic_code)
        except models.ObjectDoesNotExist:
            message.forward(reporter.connection().identity, \
                _(u"Join Error. Provided Clinic code (%(clinic)s) is wrong.") % {'clinic': clinic_code})
            return True
    
        # check that location is a clinic (not sure about that)
        if not clinic.type in LocationType.objects.filter(name='Clinic'):
            message.forward(reporter.connection().identity, \
                _(u"Join Error. You must provide a Clinic code."))
            return True

        # set location
        reporter.location = clinic

        # check role code
        try:
            role  = Role.objects.get(code=role_code)
        except models.ObjectDoesNotExist:
            message.forward(reporter.connection().identity, \
                _(u"Join Error. Provided Role code (%(role)s) is wrong.") % {'role': role_code})
            return True

        reporter.role   = role

        # set account active
        # /!\ we use registered_self as active
        reporter.registered_self  = True

        # save modifications
        reporter.save()

        # inform target
        message.forward(reporter.connection().identity, \
            _("Success. You are now registered as %(role)s at %(clinic)s with alias @%(alias)s.") % {'clinic': clinic, 'role': reporter.role, 'alias': reporter.alias})

        #inform admin
        if message.persistant_connection.reporter != reporter:
            message.respond( \
            _("Success. %(reporter)s is now registered as %(role)s at %(clinic)s with alias @%(alias)s.") % {'reporter': reporter, 'clinic': clinic, 'role': reporter.role, 'alias': reporter.alias})
        return True

    def respond_to_join(self, message, info):
        message.respond(
           _("%(mobile)s registered to @%(username)s " +
              "(%(user_last_name)s, %(user_first_name)s) at %(clinic)s.") % info)
        
    @keyword(r'confirm (\w+)')
    def confirm_join (self, message, username):
        mobile   = message.peer
        try:
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            self.respond_not_registered(username)
        for provider in Provider.objects.filter(mobile=mobile):
            if provider.user.id == user.id:
                provider.active = True
            else:
                provider.active = False
            provider.save()
        info = provider.get_dictionary()
        self.respond_to_join(message, info)
        log(provider, "confirmed_join")
        return True

    
    def respond_not_registered (self, message, target):
        raise HandlerFailed(_("User @%s is not registered.") % target)

    def find_provider (self, target):
        try:
            if re.match(r'^\d+$', target):
                reporter = Reporter.objects.get(id=target)
            else:
                reporter = Reporter.objects.get(alias__iexact=target)                
            return reporter
        except models.ObjectDoesNotExist:
            # FIXME: try looking up a group
            self.respond_not_registered(message, target)

    @keyword(r'\@(\w+) (.+)')
    @registered
    def direct_message (self, message, target, text):
        provider = self.find_provider(target)
        try:
            mobile = provider.mobile
        except:
            self.respond_not_registered(message, target)
        sender = message.sender.username
        return message.forward(mobile, "@%s> %s" % (sender, text))
        

    # Register a new patient
    @keyword(r'new (\S+) (\S+) ([MF]) ([\d\-]+)( \D+)?( \d+)?( z\d+)?')
    @registered
    def new_case (self, message, last, first, gender, dob,
                  guardian="", contact="", zone=None):
        # reporter
        reporter    = message.persistant_connection.reporter
        
        
        dob = re.sub(r'\D', '', dob)
        try:
            dob = time.strptime(dob, "%d%m%y")
        except ValueError:
            try:
                dob = time.strptime(dob, "%d%m%Y")
            except ValueError:
                raise HandlerFailed(_("Couldn't understand date: %s") % dob)
        dob = datetime.date(*dob[:3])
        if guardian:
            guardian = guardian.title()
        # todo: move this to a more generic get_description
        info = {
            "first_name" : first.title(),
            "last_name"  : last.title(),
            "gender"     : gender.upper()[0],
            "dob"        : dob,
            "guardian"   : guardian,
            "mobile"     : contact,
            "reporter"   : reporter,
            "location"       : reporter.location
        }

        ## check to see if the case already exists
        iscase = Case.objects.filter(first_name=info['first_name'], last_name=info['last_name'], reporter=info['reporter'], dob=info['dob'])
        if iscase:
            #message.respond(_(
            #"%(last_name)s, %(first_name)s has already been registered by you.") % info)
            info["PID"] = iscase[0].ref_id
            self.info(iscase[0].id)
            self.info(info)
            message.respond(_(
            "%(last_name)s, %(first_name)s (+%(PID)s) has already been registered by %(reporter)s.") % info)
            # TODO: log this message
            return True
        case = Case(**info)
        case.save()

        info.update({
            "id": case.ref_id,
            "last_name": last.upper(),
            "age": case.age()
        })
        
        message.respond(_(
            "New +%(id)s: %(last_name)s, %(first_name)s %(gender)s/%(age)s " +
            "(%(guardian)s) %(location)s") % info)
        
        log(case, "patient_created")
        return True

    def find_case (self, ref_id):
        try:
            return Case.objects.get(ref_id=int(ref_id))
        except Case.DoesNotExist:
            raise HandlerFailed(_("Case +%s not found.") % ref_id)

    @keyword(r'cancel \+?(\d+)')
    @authenticated
    def cancel_case (self, message, ref_id):
        case = self.find_case(ref_id)
        if case.reportmalnutrition_set.count():
            raise HandlerFailed(_(
                "Cannot cancel +%s: case has malnutrition reports.") % ref_id)
                
        if case.reportmalaria_set.count():
            raise HandlerFailed(_(
                "Cannot cancel +%s: case has malaria reports.") % ref_id)
                
        if case.reportdiagnosis_set.count():
            raise HandlerFailed(_(
                "Cannot cancel +%s: case has diagnosis reports.") % ref_id)

        case.delete()
        message.respond(_("Case +%s cancelled.") % ref_id)
        
        
        log(message.sender.provider, "case_cancelled")        
        return True
    
    @keyword(r'inactive \+?(\d+)?(.+)')
    @authenticated
    def inactive_case (self, message, ref_id, reason=""):
        case = self.find_case(ref_id)
        case.set_status(Case.STATUS_INACTIVE)
        case.save()
        info = case.get_dictionary()
        message.respond(_(
            "+%(ref_id)s: %(last_name)s, %(first_name)s %(gender)s/%(months)s " +
            "(%(guardian)s) has been made inactive") % info)
        return True

    @keyword(r'transfer \+?(\d+) (?:to )?\@?(\w+)')
    @registered
    def transfer_case (self, message, ref_id, target):
        reporter    = message.persistant_connection.reporter
        case = self.find_case(ref_id)
        new_provider = self.find_provider(target) 
        case.reporter = new_provider
        case.save()
        info = {
            'username': new_provider.alias,
            'name': new_provider.full_name(),
            'location':new_provider.location
        }
        info["ref_id"] = case.ref_id
        message.respond(_("Case +%(ref_id)s transferred to @%(username)s " +
                         "(%(name)s - %(location)s).") % info)
        
        message.forward(new_provider.connection().identity,
                        _("Case +%s transferred to you from @%s (%s - %s).")%
                        (case.ref_id, reporter.alias, reporter.full_name(), reporter.location))
        
        log(case, "case_transferred")        
        return True
 
    @keyword(r's(?:how)? \+?(\d+)')
    @registered
    def show_case (self, message, ref_id):
        case = self.find_case(ref_id)
        info = case.get_dictionary()

        message.respond(_(
            "+%(ref_id)s %(status)s %(last_name)s, %(first_name)s "
            "%(gender)s/%(age)s %(guardian)s - %(location)s") % info)        
        
        return True
    
    @keyword(r'n(?:ote)? \+(\d+) (.+)')
    @registered
    def note_case (self, message, ref_id, note):
        reporter    = message.persistant_connection.reporter
        case = self.find_case(ref_id)
        CaseNote(case=case, created_by=reporter, text=note).save()
        message.respond(_("Note added to case +%s.") % ref_id)
        
        log(case, "note_added")        
        return True

    @keyword(r'd \+(\d+ )(.*)')
    @authenticated
    def diagnosis(self, message, ref_id, text):
        case = self.find_case(ref_id)
        provider = message.sender.provider
        diags = []
        labs = []

        hits = find_diagnostic_re.findall(message.text)
        for hit in hits:
            code = hit[2:]
            try:
                diags.append(Diagnosis.objects.get(code__iexact=code))
            except Diagnosis.DoesNotExist:
                raise HandlerFailed("Unknown diagnosis code: %s" % code)

        hits = find_lab_re.findall(text)
        for hit in hits:
            code, sign, number = hit
            try:
                # the code starts with /
                labs.append([Lab.objects.get(code__iexact=code[1:]), sign, number])
            except Lab.DoesNotExist:
                raise HandlerFailed("Unknown lab code: %s" % code)

        self.delete_similar(case.reportdiagnosis_set)
        report = ReportDiagnosis(case=case, provider=provider, text=message.text)
        report.save()
        for diag in diags:
            report.diagnosis.add(diag)
        for lab, sign, number in labs:
            ld = LabDiagnosis()
            ld.lab = lab
            ld.result = int(sign == "+")
            if number:
                ld.amount = number
            ld.diagnosis = report
            ld.save()
        report.save()

        info = case.get_dictionary()
        info.update(report.get_dictionary())
        if info["labs_text"]:
            info["labs_text"] = "%sLabs: %s" % (info["diagnosis"] and " " or "", info["labs_text"])

        message.respond(_("D> +%(ref_id)s %(first_name_short)s.%(last_name)s %(diagnosis)s%(labs_text)s") % info)
        
        # add in the forward of instructions to the case provider
        # if that it is not the reporter of the issue        

        
        instructions = []       
        for diagnosis in report.diagnosis.all():
            if diagnosis.instructions:
                instructions.append(diagnosis.instructions)

        if instructions:
            if provider != case.provider:
                # there's a different provider
                info = {"ref_id":ref_id, "instructions":(", ".join(instructions))}
                message.forward(case.provider.mobile, "D> +%(ref_id)s %(instructions)s" % info)
                
                
        log(case, "diagnosis_taken")        
        return True            

    # DIARRHEA
    # follow up on diarrhea
    @keyword(r'ors \+(\d+) ([yn])')
    @authenticated
    def followup_diarrhea(self, message, ref_id, is_ok):
        case    = self.find_case(ref_id)
        is_ok   = True if is_ok == "y" else False

        provider = message.sender.provider
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
                    
        log(case, "diarrhea_fu_taken")
        return True

    @keyword(r'ors \+(\d+) ([yn]) (\d+)\s?([a-z\s]*)')
    @authenticated
    def report_diarrhea(self, message, ref_id, ors, days, complications):
        case = self.find_case(ref_id)

        ors     = True if ors == "y" else False
        days    = int(days)

        observed, choices = self.get_diarrheaobservations(complications)
        self.delete_similar(case.reportdiarrhea_set)

        provider = message.sender.provider
        report = ReportDiarrhea(case=case, provider=provider, ors=ors, days=days)
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

    def get_diarrheaobservations(self, text):
        choices  = dict( [ (o.letter, o) for o in DiarrheaObservation.objects.all() ] )
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
