#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from datetime import date, datetime

import rapidsms
from rapidsms.parsers.keyworder import * 
from django.utils.translation import ugettext as _

from apps.reporters.models import *
from apps.locations.models import *
from apps.rdtreporting.models import *
from apps.rdtreporting.utils import *

class HandlerFailed (Exception):
    pass

class MalformedRequest (Exception):
    pass

def registered (func):
    def wrapper (self, message, *args):
        if message.persistant_connection.reporter:
            return func(self, message, *args)
        else:
            message.respond(_(u"Sorry, only registered users can access this program."))
            return True
    return wrapper

def admin (func):
    def wrapper (self, message, *args):
        reporter = message.persistant_connection.reporter
        if reporter and ReporterGroup.objects.get(title='admin') in reporter.groups.only():
            return func(self, message, *args)
        else:
            message.respond(_(u"Sorry, only administrators of the system can perform this action."))
            return False
    return wrapper


class App (rapidsms.app.App):

    keyword = Keyworder()

    def start (self):
        pass

    def handle (self, message):
        try:
            func, captures = self.keyword.match(self, message.text)
        except TypeError:
            # didn't find a matching function
            message.respond(_(u"Error. Your message could not be recognized by the system. Please check syntax and retry."))
            return False
        try:
            handled = func(self, message, *captures)
        except HandlerFailed, e:
            print e
            handled = True
        except Exception, e:
            print e
            message.respond(_(u"An error has occured (%(e)s).") % {'e': e})
            raise
        message.was_handled = bool(handled)
        return handled

    # JOIN
    keyword.prefix = ["subscribe", "join"]
    @keyword(r'(\w+)\s?(\w*)')
    @registered
    def join(self, message, clinic_code, role_code):
        ''' Adds a self-registered reporter to the mrdt system '''

        if role_code == None or role_code.__len__() < 1:
            role_code   = 'hw'

        reporter    = message.persistant_connection.reporter

        return self.join_reporter(message, reporter, clinic_code, role_code)

    # JOIN (ADMIN)
    keyword.prefix = ["subscribe", "join"]
    @keyword(r'\+(numbers) (letters)\s?(\w*)')
    @registered
    @admin
    def join_one(self, message, reporter_id, clinic_code, role_code):
        ''' Adds an arbitrary reporter to the mrdt system '''

        if role_code == None or role_code.__len__() < 1:
            role_code   = 'hw'

        try:
            reporter    = Reporter.objects.get(id=reporter_id)
        except models.ObjectDoesNotExist:
            message.respond(_("Join Error. The provided ID (%(id)s) does not exist in the system") % {'id': reporter_id})
            return True

        return self.join_reporter(message, reporter, clinic_code, role_code)
        
    def join_reporter(self, message, reporter, clinic_code, role_code):
        ''' sets a location and role for a reporter and mark him active '''

        # check clinic code
        try:
            clinic  = Location.objects.get(code=clinic_code)
        except models.ObjectDoesNotExist:
            message.forward(reporter.connection().identity, \
                _(u"Join Error. Provided Clinic code (%(clinic)s)is wrong.") % {'clinic': clinic_code})
            return True
    
        # check that location is a clinic (not sure about that)
        if not clinic.type in LocationType.objects.filter(name__startswith='HC'):
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
            _("Success. You are now registered as %(role)s at %(clinic)s with ID +%(id)s.") % {'clinic': clinic, 'role': reporter.role, 'id': reporter.id})

        #inform admin
        if message.persistant_connection.reporter != reporter:
            message.respond( \
            _("Success. %(reporter)s is now registered as %(role)s at %(clinic)s with ID +%(id)s.") % {'reporter': reporter, 'clinic': clinic, 'role': reporter.role, 'id': reporter.id})
        return True

    # STOP
    keyword.prefix = ["stop", "pause"]
    @keyword.blank()
    @registered
    def stop(self, message):
        ''' Disables the sender in the system '''

        reporter    = message.persistant_connection.reporter

        return self.stop_reporter(message, reporter)

    # STOP (ADMIN)
    keyword.prefix = ["stop", "pause"]
    @keyword(r'\+(numbers)')
    @registered
    @admin
    def stop_one(self, message, reporter_id):
        ''' Disables an arbitrary reporter in the system '''

        try:
            reporter    = Reporter.objects.get(id=reporter_id)
        except models.ObjectDoesNotExist:
            message.respond(_("Stop Error. The provided ID (%(id)s) does not exist in the system") % {'id': reporter_id})
            return True

        return self.stop_reporter(message, reporter)

    def stop_reporter(self, message, reporter):
        ''' mark a reporter innactive in the system '''

        if not reporter.registered_self:
            message.respond(_("%(reporter)s is already inactive.") % {'reporter': reporter})
            return True

        # set account inactive
        # /!\ we use registered_self as active
        reporter.registered_self  = False

        # save modifications
        reporter.save()

        # inform target
        message.forward(reporter.connection().identity, \
            _("Success. You are now out of the system. Come back by sending BACK."))

        #inform admin
        if message.persistant_connection.reporter != reporter:
            message.respond( \
            _("Success. %(reporter)s is now out of the system.") % {'reporter': reporter})
        return True

    # BACK
    keyword.prefix = ["back", "resume"]
    @keyword.blank()
    @registered
    def back(self, message):
        ''' Enables again the sender in the system '''

        reporter    = message.persistant_connection.reporter

        return self.back_reporter(message, reporter)

    # BACK (ADMIN)
    keyword.prefix = ["back", "resume"]
    @keyword(r'\+(numbers)')
    @registered
    @admin
    def back_one(self, message, reporter_id):
        ''' Enables again an arbitrary reporter in the system '''

        try:
            reporter    = Reporter.objects.get(id=reporter_id)
        except models.ObjectDoesNotExist:
            message.respond(_("Stop Error. The provided ID (%(id)s) does not exist in the system") % {'id': reporter_id})
            return True

        return self.back_reporter(message, reporter)

    def back_reporter(self, message, reporter):
        ''' mark a reporter active in the system '''

        if reporter.registered_self:
            message.respond(_("%(reporter)s is already active.") % {'reporter': reporter})
            return True

        # set account inactive
        # /!\ we use registered_self as active
        reporter.registered_self  = True

        # save modifications
        reporter.save()

        # inform target
        message.forward(reporter.connection().identity, \
            _("Success. You are back in the system with ID %(id)s.") % {'id': reporter.id})

        #inform admin
        if message.persistant_connection.reporter != reporter:
            message.respond( \
            _("Success. %(reporter)s is back as %(role)s at %(clinic)s.") % {'reporter': reporter, 'clinic': reporter.location, 'role': reporter.role})
        return True

    # LOOKUP
    keyword.prefix = ["lookup", "search"]
    @keyword(r'(letters)\s?(\w*)')
    @registered
    def back(self, message, clinic_code, name):
        ''' List reporters from a location matching a name '''

        # check clinic code
        try:
            clinic  = Location.objects.get(code=clinic_code)
        except models.ObjectDoesNotExist:
            message.forward(reporter.connection().identity, \
                _(u"Lookup Error. Provided Clinic code (%(clinic)s)is wrong.") % {'clinic': clinic_code})
            return True

        # get list of reporters
        reporters   = Reporter.objects.filter(location=clinic, registered_self=True)
        print reporters
        if name != None and name.__len__() > 0:
            print name
            reporters   = reporters.filter(first_name__contains=name)
            print reporters

        if reporters.__len__() == 0:
            message.respond(_("No such people at %(clinic)s.") % {'clinic': clinic})
            return True           
        
        msg     = ""
        msg_stub= _(u"%(reporter)s/%(id)s is %(role)s at %(clinic)s with %(number)s")

        # construct answer
        for areporter in reporters:
            mst     = msg_stub % {'reporter': areporter, 'id': areporter.id, 'role': areporter.role.code.upper(), 'clinic': areporter.location.code.upper(), 'number': areporter.connection().identity}
            if msg.__len__() == 0:
                msg = mst
            else:
                msg = _(u"%s, %s") % (msg, mst)

        # strip long list
        if msg.__len__() >= 160:
            intro   = _("%(nb)s results. ") % {'nb': reporters.__len__()}
            msg     = intro + msg[:-intro.__len__()]

        # answer
        message.respond(msg)
        
        return True

    # REGISTERING MRDT
    keyword.prefix = ["rdt", "mrdt"]
    @keyword(r'([0-9]{6}) (numbers) (numbers) (numbers) (numbers)')
    @registered
    def back(self, message, date, tested, confirmed, treatments, used):
        ''' List reporters from a location matching a name '''

        reporter    = message.persistant_connection.reporter
        
        try:
            report, overwritten = record_mrdt(reporter, tested, confirmed, treatments, used, day=date, overwrite=True)
        except UnknownReporter:
            message.respond(_(u"Report Failed. You are not allowed to report MRDT."))
            return True
        except DuplicateReport:
            message.respond(_(u"Report Failed. Your datas for %(date)s have already been reported.") % {'date': date})
            return True
        except ErroneousDate:
            message.respond(_(u"Report Failed. Provided date (%(date)s is erroneous.)") % {'date': date})
            return True
        except IncoherentValue:
            message.respond(_(u"Report Failed. Provided values are incoherent."))
            return True

        if overwritten:
            suffix  = _(u" (overwrite)")
        else:
            suffix  = ""

        message.respond(_("Clinic #%(clinic_id)s %(clinic)s %(date)s report received%(overwrite_suffix)s! Cases=%(tested)s, Positive=%(confirmed)s Treatment=%(treatments)s, Tests=%(used)s") % {'clinic_id': report.reporter.location.id, 'clinic': report.reporter.location, 'date': report.date.strftime("%d.%m.%Y"), 'overwrite_suffix': suffix, 'tested': report.tested, 'confirmed': report.confirmed, 'treatments': report.treatments, 'used': report.used})

        return True

        


