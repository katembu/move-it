#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

class CCForm(object):
    #KEYWORDS = {}
    MULTIPLE_PATIENTS = True
    
    def pre_process(self, message, health_id, params):
        pass
        
    def process(self, message, patient, params):
        pass

    def post_process(self, reports_list):
        pass


