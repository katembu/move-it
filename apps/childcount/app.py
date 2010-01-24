import rapidsms
from rapidsms.parsers.keyworder import Keyworder

from django.db import models

from functools import wraps

from childcount.core.models.Config import Configuration as Cfg

from reporters.models import Reporter, Role
from location.models import Location

class HandlerFailed (Exception):
    pass


def registered(func):
    ''' decorator checking if sender is allowed to process feature.

    checks if a reporter is attached to the message

    return function or boolean '''

    @wraps(func)
    def wrapper(self, message, *args):
        if message.persistant_connection.reporter:
            return func(self, message, *args)
        else:
            message.respond(_(u"Sorry, only registered users can access this"\
                              " program.%(msg)s") % {'msg': ""})

            return True
    return wrapper


class App (rapidsms.app.App):
    """Main ChildCount App
    """

    MAX_MSG_LEN = 140
    keyword = Keyworder()
    handled = False

    def start(self):
        """Configure your app in the start phase."""
        pass

    def parse(self, message):
        """Parse and annotate messages in the parse phase."""
        pass

    def handle(self, message):

        ''' Function selector

        Matchs functions with keyword using Keyworder
        Replies formatting advices on error
        Return False on error and if no function matched '''
        try:
            func, captures = self.keyword.match(self, message.text)
        except TypeError:
            # didn't find a matching function
            # make sure we tell them that we got a problem
            command_list = [method for method in dir(self) \
                            if hasattr(getattr(self, method), "format")]
            input_text = message.text.lower()
            for command in command_list:
                format = getattr(self, command).format
                try:
                    first_word = (format.split(" "))[0]
                    if input_text.find(first_word) > -1:
                        message.respond(format)
                        return True
                except:
                    pass
            return False
        try:
            self.handled = func(self, message, *captures)
        except HandlerFailed, e:
            message.respond(e.message)

            self.handled = True
        except Exception, e:
            # TODO: log this exception
            # FIXME: also, put the contact number in the config
            message.respond(_("An error occurred. Please call %(mobile)s") \
                            % {'mobile': Cfg.get('developer_mobile')})

            raise
        message.was_handled = bool(self.handled)
        return self.handled

    def cleanup(self, message):
        """Perform any clean up after all handlers have run in the
           cleanup phase."""
        pass

    def outgoing(self, message):
        """Handle outgoing message notifications."""
        pass

    def stop(self):
        """Perform global app cleanup when the application is stopped."""
        pass

    keyword.prefix = ['join']

    @keyword('(\S+) (\S+) (\S+)(?: ([a-z]\w+))?')
    def join(self, message, location_code, last_name, first_name, role=None):
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
    join.format = "join [location code] [last name] [first name] " \
                  "[role - leave blank for CHEW]"