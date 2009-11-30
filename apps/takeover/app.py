#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import rapidsms
from rapidsms.parsers.keyworder import Keyworder
from django.utils.translation import ugettext as _
from django.db import models
from reporters.models import PersistantBackend, Reporter
from childcount.models.logs import MessageLog

import re

class HandlerFailed (Exception):
    pass

from functools import wraps

def adeco(func):
    @wraps(func)
    def wrapper(self, *args):
        print("A decorator func")
        print func.__doc__
        return func(self, *args)
    return wrapper

def anotherdeco(func):
    @wraps(func)
    def wrapper(self, *args):
        print("Another decorator func")        
        print func.__doc__
        return func(self, *args)
    return wrapper

def registered (func):
    @wraps(func)
    def wrapper (self, message, *args):
        if message.persistant_connection.reporter:
            return func(self, message, *args)
        else:
            message.respond(_(u"%s")%"Sorry, only registered users can access this program.")
            return True
    return wrapper


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

    
    @keyword(r'takeover (\w+)')
    #uncomment this to test multiple decorators- was a test for eliane by ukanga.
    #@adeco
    #@registered
    #@anotherdeco
    def reporter_http_identity(self, message, username):
        """Hello World! This is a docstring"""
        reporter = self.find_provider(message, username)
        # attach the reporter to the current connection
        if PersistantBackend.from_message(message).title == "http":
            mobile = reporter.connection().identity
            if mobile == message.persistant_connection.identity:
                message.respond("You already have a http identity!")
            elif mobile[0] == "+" and mobile[1:] == message.persistant_connection.identity: 
                message.persistant_connection.reporter = reporter
                message.persistant_connection.save()
                message.respond("You now have a http identity!")
            else:
                message.respond("Illegal Operation!")
        else:
            message.respond("Operation not allowed under this mode!")
        return True
   
    def respond_not_registered (self, message, target):
        raise HandlerFailed(_("User @%s is not registered.") % target)

    def find_provider (self, message, target):
        try:
            if re.match(r'^\d+$', target):
                reporter = Reporter.objects.get(id=target)
            else:
                reporter = Reporter.objects.get(alias__iexact=target)                
            return reporter
        except models.ObjectDoesNotExist:
            # FIXME: try looking up a group
            self.respond_not_registered(message, target)