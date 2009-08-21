# coding=utf-8

import rapidsms
from utils import *

def import_function(func):
    if func.find('.') == -1:
        f   = eval(func)
    else:
        s   = func.rsplit(".", 1)
        x   = __import__(s[0], fromlist=[s[0]])
        f   = eval("x.%s" % s[1])
    return f

class App (rapidsms.app.App):

    def configure (self, function='nothing'):
        try:
            self.func       = import_function(function)
        except:
            self.func       = nothing

    def parse (self, message):
        message.idswitch    = self.func

