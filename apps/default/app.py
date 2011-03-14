#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.utils.translation import ugettext as _, activate

import rapidsms

class App(rapidsms.app.App):
    """When an incoming message is received, this application is notified
       last, to send a default response in case no other App responded."""
    
    PRIORITY = "lowest"
    
    def handle(self, msg):
        if not msg.responses:
            
            msg.respond(_("Sorry, we didn't understand that message."), 'error')
            return True
