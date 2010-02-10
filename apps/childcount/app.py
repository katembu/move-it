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


class App (rapidsms.app.App):
    """Main ChildCount App
    """
    DEFAULT_LANGUAGE = 'en'
    
    COMMANDS = [RegistrationCommand, WhoCommand]
    FORMS = [MUACForm]
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

            for health_id in health_ids:
                for params in forms:
                    keyword = params[0]
                    if keyword in self.form_keywords[self.MATCH_ALL_LANG_CHAR]:
                        lang = self.MATCH_ALL_LANG_CHAR
                    else:
                        lang = reporter_language
                    if lang in self.form_keywords and \
                       keyword in self.form_keywords[lang]:
                        handled = True
                        form_class = self.form_keywords[lang][keyword]
                        form_object = form_class(message, params)
                        form_object.pre_process(health_id)
                        #TODO handle pre_process failure
                        #TODO handle patient doesn't exist
                        patient = Patient.objects.get(health_id=health_id)
                        form_object.process(patient)
                    else:
                        #TODO handle bad form
                        print "Unkown form"
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
