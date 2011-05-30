#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import random
import rapidsms
import re

prefix      = re.compile(r'^fortune',re.I)
whitespace  = re.compile(r'\s+')

# Source:
# http://www.special-dictionary.com/proverbs/source/u/ugandan_proverb/2.htm
RESPONSES = [
    "A dog with a bone in his mouth cannot bite you.",
    "A roaring lion kills no game.",
    "An elephant can never fail to carry its tusks.",
    "Do not belittle what you did not cultivate.",
    "Even the mightiest eagle comes down to the treetops to rest.",
    "He who hunts two rats, catches none.",
    "He who is bitten by a snake fears a lizard.",
    "If you climb up a tree, you must climb down the same tree.",
    "When the moon is not full, the stars shine more brightly.",
    "When throne into the sea the stone said, 'after all, this is also a home.'",
]

class App(rapidsms.app.App):
    def handle(self, message):
        self.debug("got message %s", message.text)
        if prefix.search(message.text):
            response = random.choice(RESPONSES)
            if response:
                response = whitespace.sub(" ",response)
                self.debug("responding with %s", response)
                message.respond(response)
		return True
            else:
                self.warning("'fortune' program returned nothing")
