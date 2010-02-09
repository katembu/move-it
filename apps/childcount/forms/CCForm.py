#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

class CCForm(object):
    KEYWORDS = {}
    ACTIVE = True
    error = None
    report_object = None
    
    def pre_process(self,health_id,params):
        pass
        
    def process(self,patient,reporter,params):
        pass

    def post_process(self,reports_list):
        pass


