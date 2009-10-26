#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import re
from datetime import date, datetime, timedelta
from django.utils.translation import ugettext as _
from rapidsms import Message
from rapidsms.connection import *
from apps.reporters.models import *
from models import *

def diseases_from_string(text):
    ''' returns a list of Disease with numbers build from SMS-syntax
    '''
    diseases= []
    
    # split different diseases declarations
    codes   = text.split(' ')

    for code in codes:
        if code == '': continue
        try:
            # extract values: <CODE><CASES#>+<DEATHS>
            extract = re.search('([a-zA-Z]+)([0-9]+)\+?([0-9]*)', code).groups()
            abbr    = extract[0].lower()
            cases   = int(extract[1])
            deaths  = 0 if extract[2].__len__() == 0 else int(extract[2])
        except:
            raise InvalidInput

        try:
            disease = Disease.by_code(abbr)
        except Disease.DoesNotExist:
            raise IncoherentValue(_(u'FAILED: %s is not a valid disease code.  Please try again.' % abbr))

        diseases.append({'disease': disease, 'cases': cases, 'deaths': deaths})

    return diseases

def allow_me2u(message):
    ''' free2u App helper. Allow only registered users. '''

    try:
        if message.persistant_connection.reporter.registered_self:
            return True
        else:
            return False
    except:
        return False





