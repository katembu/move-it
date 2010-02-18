#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin


class CCForm(object):
    #KEYWORDS = {}
    MULTIPLE_PATIENTS = True
    PREFIX = '+'

    def __init__(self, message, params, health_id):
        self.message = message
        self.params = params
        self.health_id = health_id
        self.response = ''

    def pre_process(self):
        pass

    def process(self, patient):
        pass

    def post_process(self, forms_list):
        pass
