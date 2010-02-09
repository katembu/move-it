#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

class CCCommand(object):
    KEYWORDS = {}
    ACTIVE = True
    REGISTERED_REPORTERS_ONLY = True
    error = None
        
    def process(self,reporter,params):
        pass

