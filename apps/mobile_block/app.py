import rapidsms

class App(rapidsms.app.App):
    def handle(self, message):
        # Silently discard messages from unknown numbers.
        # We don't want to send messages back because they
        # could be used to maliciously run up our phone
        # bill.
        if not message.reporter:
            self.log("INFO", "Message from %(user)s silently " \
                "discarded" % {'user': message.connection.identity})
            return True

