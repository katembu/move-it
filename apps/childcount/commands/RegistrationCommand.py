#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

class RegistrationCommand(object):
    KEYWORDS = {
        'en': ['chw'],
    }
    ACTIVE = True
    REGISTERED_REPORTERS_ONLY = False
    error = None

    def process(self,reporter,params):
    
        print 'yea'
    
    
        #@keyword('(\S+) (\S+) (\S+)(?: ([a-z]\w+))?')
        #def join(self, message, location_code, last_name, first_name, role=None):
        ''' register as a user and join the system

        Format: join [location code] [last name] [first name]
        [role - leave blank for CHEW]

        location - it should be for the village they operate in'''

        #default alias for everyone until further notice
        username = None
        # do not skip roles for now
        role_code = role
        try:
            name = "%(fname)s %(lname)s" % {'fname': first_name, \
                                            'lname': last_name}
            # parse the name, and create a reporter
            alias, fn, ln = Reporter.parse_name(name)

            if not message.persistant_connection.reporter:
                rep = Reporter(alias=alias, first_name=fn, last_name=ln)
            else:
                rep = message.persistant_connection.reporter
                rep.alias = alias
                rep.first_name = fn
                rep.last_name = ln

            rep.save()

            # attach the reporter to the current connection
            message.persistant_connection.reporter = rep
            message.persistant_connection.save()

            # something went wrong - at the
            # moment, we don't care what
        except:
            message.respond(_("Join Error. Unable to register your account."))

        if role_code == None or role_code.__len__() < 1:
            role_code = Cfg.get('default_chw_role')

        reporter = message.persistant_connection.reporter

        # check location code
        try:
            location = Location.objects.get(code=location_code)
        except models.ObjectDoesNotExist:
            message.forward(reporter.connection().identity, \
                _(u"Join Error. Provided location code (%(loc)s) is wrong.") \
                  % {'loc': location_code})
            return True

        # check that location is a clinic (not sure about that)
        #if not clinic.type in LocationType.objects.filter(name='Clinic'):
        #    message.forward(reporter.connection().identity, \
        #        _(u"Join Error. You must provide a Clinic code."))
        #    return True

        # set location
        reporter.location = location

        # check role code
        try:
            role = Role.objects.get(code=role_code)
        except models.ObjectDoesNotExist:
            message.forward(reporter.connection().identity, \
                _(u"Join Error. Provided Role code (%(role)s) is wrong.") \
                  % {'role': role_code})
            return True

        reporter.role = role

        # set account active
        # /!\ we use registered_self as active
        reporter.registered_self = True

        # save modifications
        reporter.save()

        # inform target
        message.forward(reporter.connection().identity, \
            _("Success. You are now registered as %(role)s at %(loc)s with " \
              "alias @%(alias)s.") \
           % {'loc': location, 'role': reporter.role, 'alias': reporter.alias})

        #inform admin
        if message.persistant_connection.reporter != reporter:
            message.respond(_("Success. %(reporter)s is now registered as " \
                            "%(role)s at %(loc)s with alias @%(alias)s.") \
                            % {'reporter': reporter, 'loc': location, \
                            'role': reporter.role, 'alias': reporter.alias})
        return True
