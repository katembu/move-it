#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.utils.translation import ugettext as _

import rapidsms

class App(rapidsms.app.App):
    """When an incoming message is received, this application is notified
       last, to send a default response in case no other App responded."""
    
    PRIORITY = "lowest"
    
    def handle(self, msg):
        if not msg.responses:
            error_str = _(u"Sorry, we didn't understand that message. " \
                            "(Your message: \"")
            end_str = u"\")"
            more_str = u"..."

            max_len= 140 - len(error_str) - len(end_str) - len(more_str)

            text = msg.text[0:max_len]
            if text != msg.text:
                text += more_str

            msg.respond(error_str+text+end_str, 'error')
            return True
