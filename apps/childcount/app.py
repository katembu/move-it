#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

import re

from django.utils.translation import ugettext as _
from django.db import models

import rapidsms
from reporters.models import Reporter, Role
from locations.models import Location

from childcount.models import Configuration as Cfg
from childcount.models import Patient
from childcount.forms import *
from childcount.commands import *
from childcount.exceptions import *

class NotRegestered(Exception):
    pass

class App (rapidsms.app.App):
    """Main ChildCount App
    """
    DEFAULT_LANGUAGE = 'en'
    
    COMMANDS = [RegistrationCommand, WhoCommand]
    FORMS = [MUACForm, HealthStatusForm, FeverForm, MobileForm, NewbornForm]
    MATCH_ALL_LANG_CHAR = '*'
    
    command_keywords = {}
    form_keywords = {}

    def start(self):
        def create_mapping(cls_list):
            
            keywords = {}
            keywords[self.MATCH_ALL_LANG_CHAR] = {}
            for cls in cls_list:
                for lang in cls.KEYWORDS.keys():
                    lang = lang.lower().strip()
                    if not lang in keywords:
                        keywords[lang] = {}
                    for keyword in cls.KEYWORDS[lang]:
                        keyword = keyword.lower().strip()
                        if keyword in keywords[lang] or \
                           keyword in keywords[self.MATCH_ALL_LANG_CHAR]:
                            raise Exception(u"Keyword clash in language " \
                                             "'%(language)s' on keyword " \
                                             "'%(keyword)s' in %(class)s" % \
                                             {'language': lang, \
                                              'keyword': keyword, \
                                              'class':cls})
                        else:
                            keywords[lang][keyword] = cls
            return keywords
        self.command_keywords = create_mapping(self.COMMANDS)
        self.form_keywords = create_mapping(self.FORMS)

    def parse(self, message):
        """Parse and annotate messages in the parse phase."""
        pass

    def handle(self, message):
        FORM_PREFIX = '\+'
        handled = False
    
        reporter = message.persistant_connection.reporter
        if reporter and reporter.language:
            reporter_language = reporter.language
        else:
            reporter_language = self.DEFAULT_LANGUAGE

        # make lower case, strip, and remove duplicate spaces
        input_text = re.sub(r'\s{2,}', ' ', message.text.strip().lower())

        ### Forms
        split_regex = re.compile( \
            r'^\s*((?P<health_ids>.*?)\s*)??(?P<forms>%(form_prefix)s.*$)' % \
             {'form_prefix': FORM_PREFIX})
        forms_match = split_regex.match(input_text)

        if forms_match:
            handled = True
            
            #TODO make this form specific
            if not message.persistant_connection.reporter:
                message.respond(_(u"You must register before you can send " \
                                   "any reports."))
                raise NotRegistered
            
            health_ids_text = forms_match.groupdict()['health_ids']
            forms_text = forms_match.groupdict()['forms']
            if health_ids_text:
                health_ids = re.findall(r'\w+', health_ids_text)
            else:
                health_ids = []

            form_groups_regex = re.compile( \
                r'%(form_prefix)s\s?(\w+.*?)(?=\s*%(form_prefix)s|$)' % \
                 {'form_prefix': FORM_PREFIX})

            forms = []
            for group in form_groups_regex.findall(forms_text):
                params = re.split(r'\s+', group)
                forms.append(params)

            invalid_ids = []
            invalid_forms = []
            
            patient_bucket = {}
            form_bucket = {}
            for health_id in health_ids:
                if health_id not in patient_bucket:
                    patient_bucket[health_id] = []
                for params in forms:
                    keyword = params[0]
                    if keyword in self.form_keywords[self.MATCH_ALL_LANG_CHAR]:
                        lang = self.MATCH_ALL_LANG_CHAR
                    else:
                        lang = reporter_language
                    if lang in self.form_keywords and \
                       keyword in self.form_keywords[lang]:
                        form_class = self.form_keywords[lang][keyword]
                        form_object = form_class(message, params)
                        form_object.pre_process(health_id)
                        try:
                            patient = Patient.objects.get(health_id=health_id)
                        except Patient.DoesNotExist:
                            invalid_ids.append(health_id)
                        else:
                            try:
                                response = form_object.process(patient)
                            except (ParseError, BadValue), e:
                                form_bucket[keyword] = e.message
                            except Inapplicable, e:
                                patient_bucket[health_id].append(e.message)
                            else:
                                patient_bucket[health_id].append( \
                                    '%(prefix)s%(keyword)s[%(msg)s]' % \
                                    {'prefix':FORM_PREFIX, \
                                     'keyword':keyword.upper(), \
                                     'msg':response})
                    else:
                        invalid_forms.append(keyword)

            if len(form_bucket) > 0:
                msg = ""
                for keyword, error in form_bucket.iteritems():
                    msg += _(u" Form +%(keyword)s failed: %(error)s") % \
                            {'keyword':keyword.upper(), 'error':error}
                message.respond(msg)

            if len(patient_bucket) > 0:
                for patient, msgs in patient_bucket.iteritems():
                    if not msgs:
                        continue
                    message.respond('%(id)s: %(msgs)s' % \
                                   {'id':patient.upper(), \
                                    'msgs':' '.join(msgs)})


            invalid_forms = ['%s%s' % (FORM_PREFIX, form.upper()) for form \
                                                         in set(invalid_forms)]
            if len(invalid_forms) == 1:
                invalid_form_string = _(u"%(form)s is not a valid form. " \
                                         "Please correct and send " \
                                         "that form again.") % \
                                         {'form': invalid_forms[0]}
            elif len(invalid_forms) > 1:
                if len(invalid_forms) == 2:
                    form_string = _(u" and ").join(invalid_forms)
                else:
                    form_string = _(u"%s, and %s") % \
                        (', '.join(invalid_forms[:-1]), invalid_forms[-1])
                invalid_form_string = _(u"%(forms)s are not valid " \
                                         "forms. Please correct and " \
                                         "send those %(num)d forms again.") % \
                                         {'forms': form_string, \
                                          'num':len(invalid_forms)}

            #remove duplicates
            invalid_ids = [ id.upper() for id in set(invalid_ids)]

            if len(invalid_ids) == 1:
                invalid_id_string = _(u"%(id)s is not a valid health ID. "\
                                        "Please correct and send forms " \
                                        "for that patient again.") % \
                                         {'id': invalid_ids[0]}
            elif len(invalid_ids) > 1:
                if len(invalid_ids) == 2:
                    id_string = _(u" and ").join(invalid_ids)
                else:
                    id_string = _(u"%s, and %s") % \
                        (', '.join(invalid_ids[:-1]), invalid_ids[-1])
                invalid_id_string = _(u"%(ids)s are not valid health " \
                                         "IDs. Please correct and " \
                                         "send forms for those %(num)d " \
                                         "patients again.") % \
                                         {'ids': id_string, \
                                          'num':len(invalid_ids)}
            if invalid_forms:
                message.respond(invalid_form_string)
                                         
            if invalid_ids:
                message.respond(invalid_id_string)
            
            return True

        ### Commands
        params = re.split(r'\s+', message.text)
        command = params[0]
        if command in self.command_keywords[self.MATCH_ALL_LANG_CHAR]:
            lang = self.MATCH_ALL_LANG_CHAR
        else:
            lang = reporter_language
        if lang in self.command_keywords and \
           command in self.command_keywords[lang]:
            handled = True
            command_class = self.command_keywords[lang][command]
            command_object = command_class(message, params)
            try:
                command_object.process()
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
