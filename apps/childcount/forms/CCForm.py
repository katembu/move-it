#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

class CCForm(object):
    #KEYWORDS = {}
    MULTIPLE_PATIENTS = True
    message = None
    params = None

    def __init__(self, message, params):
        self.message = message
        self.params = params

    def pre_process(self, health_id):
        pass

    def process(self, patient):
        pass

    def post_process(self, forms_list):
        pass
