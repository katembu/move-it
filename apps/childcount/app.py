#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re
from functools import wraps

from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
from django.db import models

import rapidsms
from reporters.models import Reporter, Role
from locations.models import Location
from childcount.models import Configuration as Cfg
from childcount.models import Patient
from childcount.forms import *
from childcount.commands import *
from childcount.exceptions import *
from childcount.utils import respond_exceptions, KeywordMapper


class App (rapidsms.app.App):
    """Main ChildCount App
    """
    DEFAULT_LANGUAGE = 'en'
    FORM_PREFIX = '+'

    commands = []
    forms = []



    def configure(self, title='ChildCount', tab_link='/childcount', \
                  forms=None, commands=None):
        if forms is not None:
            forms = forms.replace(' ', '').split(',')
            for form in forms:
                try:
                    self.forms.append(eval(form))
                except NameError:
                    self.debug(_(u'%s form not found') % form)
        if commands is not None:
            commands = commands.replace(' ', '').split(',')
            for command in commands:
                try:
                    self.commands.append(eval(command))
                except:
                    self.debug(_(u'%s command not found') % command)


    def start(self):
        self.command_mapper = KeywordMapper()
        self.form_mapper = KeywordMapper()
        self.form_mapper.add_classes(self.forms)
        self.command_mapper.add_classes(self.commands)

    def parse(self, message):
        """Parse and annotate messages in the parse phase."""
        pass

    @respond_exceptions
    def handle(self, message):

        handled = False

        reporter = message.persistant_connection.reporter
        if reporter and reporter.language:
            lang = reporter.language
        else:
            lang = self.DEFAULT_LANGUAGE

        # make lower case, strip, and remove duplicate spaces
        input_text = re.sub(r'\s{2,}', ' ', message.text.strip().lower())

        ### Forms
        split_regex = re.compile( \
         r'^\s*((?P<health_ids>.*?)\s*)??(?P<forms>%(form_prefix)s.*$)' % \
             {'form_prefix': re.escape(self.FORM_PREFIX)})
        forms_match = split_regex.match(input_text)

        if forms_match:
            handled = True

            #TODO make this form specific
            if not message.persistant_connection.reporter:
                message.respond(_(u"You must register before you can send " \
                                   "any reports."))
                return handled

            health_ids_text = forms_match.groupdict()['health_ids']
            forms_text = forms_match.groupdict()['forms']
            if health_ids_text:
                health_ids = re.findall(r'\w+', health_ids_text)
            else:
                health_ids = []

            form_groups_regex = re.compile( \
                r'%(form_prefix)s\s?(\w+.*?)(?=\s*%(form_prefix)s|$)' % \
                 {'form_prefix': re.escape(self.FORM_PREFIX)})

            forms = []
            for group in form_groups_regex.findall(forms_text):
                params = re.split(r'\s+', group)
                forms.append(params)


            # okay, health_ids is a list containing all health ids:
            # i.e: ['df2d', 'se23', 'di24']


            # forms is a list of lists containing the forms and
            # thier params:
            # i.e: [['birth', 'p', 'm'], ['h', 'y'], ['mob', '12345678']]


            # Write now, we are only going to accept a single health ID.
            if len(health_ids) != 1:
                message.respond(_(u"Error: Could not understand your " \
                                   "message. Your message must start with " \
                                   "a single health ID, followed by a space " \
                                   "then a %(pre)s then the form keyword " \
                                   "you are sending.") % \
                                   {'pre': self.FORM_PREFIX})
                return handled
            health_id = health_ids[0]

            failed_forms = []
            successful_forms = []

            for params in forms:
                keyword = params[0]

                if keyword not in self.form_mapper.get_keywords(lang):
                    failed_forms.append({'keyword': keyword, \
                                         'error': _(u"Not a recognised form")})
                    continue
                cls = self.form_mapper.get_class(lang, keyword)
                obj = cls(message, params, health_id)

                # First process.  This is where PatientRegistration will
                # create the patient records
                try:
                    obj.pre_process()
                except (ParseError, BadValue, Inapplicable), e:
                    pretty_form = '%s%s' % (self.FORM_PREFIX, \
                                            keyword.upper())

                    message.respond(_(u"Error while processing %(frm)s: " \
                                       "%(e)s - Please correct and send all " \
                                       "information again.") % \
                                       {'frm': pretty_form, 'e': e.message})
                    return handled

                try:
                    patient = Patient.objects.get(health_id__iexact=health_id)
                except Patient.DoesNotExist:
                    message.respond(_(u"%(id)s is not a valid Health ID. " \
                                       "Please check and try again.") % \
                                       {'id': health_id})
                    return handled

                try:
                    obj.process(patient)
                except (ParseError, BadValue, Inapplicable), e:
                    failed_forms.append({'keyword': keyword, \
                                         'error': e.message, 'e': e})
                else:
                    successful_forms.append({'keyword': keyword, \
                                             'response': obj.response, \
                                             'obj': obj})

            successful_string = ''
            if successful_forms:
                keywords = [self.FORM_PREFIX + f['keyword'].upper() \
                                                   for f in successful_forms]
                successful_string += ', '.join(keywords) + \
                                                _(u" successfuly processed:")

                for form in successful_forms:
                    successful_string += ' [%s]' % form['response']

            failed_string = ''
            send_again = False
            for form in failed_forms:
                failed_string += ' %(pre)s%(keyword)s failed: %(error)s' % \
                                 {'pre': self.FORM_PREFIX, \
                                  'keyword': form['keyword'].upper(), \
                                  'error': form['error']}
                if 'e' in form and not isinstance(form['e'], Inapplicable):
                    send_again = True
            if send_again and len(failed_forms) == 1:
                failed_string += _(" You must send that form again.")
            elif send_again and len(failed_forms) > 1:
                failed_string += _(" You must send those forms again.")

            if not (successful_forms and failed_forms):
                message.respond(successful_string + failed_string)
                return handled
            else:
                if len(failed_forms) == 1:
                    cnt_failed = _(u"1 form failed")
                else:
                    cnt_failed = _(u"%d forms failed") % len(failed_forms)

                if len(successful_forms) == 1:
                    cnt_successful = _(u"1 successful")
                else:
                    cnt_successful = _(u"%d forms successful") % \
                                                        len(successful_forms)
                response = u"%s, %s" % (failed_string, successful_string)
                message.respond(response)
            return handled


        ### Commands
        params = re.split(r'\s+', input_text)
        command = params[0]
        if command in self.command_mapper.get_keywords(lang):
            handled = True
            cls = self.command_mapper.get_class(lang, command)
            obj = cls(message, params)
            try:
                obj.process()
            except (ParseError, BadValue), e:
                message.respond(e.message)
        return handled

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
