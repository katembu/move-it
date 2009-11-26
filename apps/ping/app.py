#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import rapidsms
import re
from datetime import datetime

def import_function(func):
    if func.find('.') == -1:
        f   = eval(func)
    else:
        s   = func.rsplit(".", 1)
        x   = __import__(s[0], fromlist=[s[0]])
        f   = eval("x.%s" % s[1])
    return f

def parse_numbers(sauth):
    nums    = sauth.replace(" ","").split(",")
    for num in nums:
        if num == "": nums.remove(num)
    return nums

class App (rapidsms.app.App):

    def configure (self, auth_func=None, auth=None):
        ''' set up authentication mechanism
            configured from [ping] in rapidsms.ini '''
    
        # add custom function
        try:
            self.func       = import_function(auth_func)
        except:
            self.func       = None
        
        # add defined numbers to a list
        try:
            self.allowed    = parse_numbers(auth)
        except:
            self.allowed    = []

        # allow everybody trigger
        self.allow          = ('*','all','true','True').count(auth) > 0

        # deny everybody trigger
        self.disallow       = ('none','false','False').count(auth) > 0
        

    def handle (self, message):
        ''' check authorization and respond 
            if auth contained deny string => return
            if auth contained allow string => answer
            if auth contained number and number is asking => reply
            if auth_func contained function and it returned True => reply
            else return'''

        # We only want to answer ping alone, or ping followed by a space and other characters
        if not re.match(r'^ping( +|$)', message.text.lower()):
            return False
        
        identifier_match = re.match(r'^ping +(?P<identifier>\w+).*$', message.text.lower())
        if not identifier_match:
            identifier = False
        else: 
            identifier = identifier_match.groupdict()['identifier']
        
        # deny has higher priority
        if self.disallow:
            return False

        # allow or number in auth= or function returned True
        if self.allow or \
            (self.allowed and self.allowed.count(message.peer) > 0) or \
            (self.func and self.func(message)):

            now = datetime.now()
            if identifier:                
                message.respond("pong %s on %s" % (identifier, now.strftime("%c")))
            else:
                message.respond("pong on %s" % now.strftime("%c"))
            return True
