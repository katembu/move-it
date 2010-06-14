#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin


class CCForm(object):
    #KEYWORDS = {}
    MULTIPLE_PATIENTS = True
    PREFIX = '+'

    def __init__(self, message, date, chw, params, health_id):
        self.message = message
        self.date = date
        self.chw = chw
        self.params = params
        self.health_id = health_id
        self.encounter = None
        self.form_group = None
        self.response = ''

    def pre_process(self):
        pass

    def process(self, patient):
        pass

    def post_process(self, forms_list):
        pass
