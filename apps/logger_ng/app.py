#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import rapidsms

from logger_ng.models import LoggedMessage


class App(rapidsms.app.App):
    '''
    TODO
    '''

    def ajax_POST_send_message(self, urlparser, post):
        """
        Callback method for sending messages from the logger web-interface
        via the ajax app.
        """
        try:
            msg = LoggedMessage.objects.get(pk=post["msg_pk"])
        except LoggedMessage.DoesNotExist:
            return

        be = self.router.get_backend(msg.backend)
        if not be:
            return

        new_msg = be.message(msg.identity, post["text"])
        new_msg.logger_id = msg.pk
        new_msg.status = LoggedMessage.STATUS_LOGGER_RESPONSE
        new_msg.send()

    def handle(self, message):
        '''
        This will be called when messages come in.
        '''
        msg = LoggedMessage.create_from_message(message)
        msg.direction = LoggedMessage.DIRECTION_INCOMING
        msg.save()

        # Watermark the message object with the LoggedMessage pk.
        message.logger_id = msg.pk

        # Print message if debug
        self.debug(msg)

    def outgoing(self, message):
        '''
        This will be called when messages go out.
        '''
        msg = LoggedMessage.create_from_message(message)
        msg.direction = LoggedMessage.DIRECTION_OUTGOING

        # If an _outgoing_ message has a logger_id it is actually the logger_id
        # of the incoming message (because message.respond does a copy.copy
        # on the message object).
        if hasattr(message, 'logger_id'):
            try:
                orig_msg = LoggedMessage.incoming.get(pk=message.logger_id)
            except LoggedMessage.DoesNotExist:
                pass
            else:
                msg.response_to = orig_msg

        msg.save()

        # Watermark the message object with the LoggedMessage pk.
        message.logger_id = msg.pk

        # Print message if debug
        self.debug(msg)
