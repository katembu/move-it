#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from cc.decorators import *

class CCCommand(object):
    KEYWORDS = {}
       
    @registered
    @admin
    
    def process(self,message,params):
        pass
        

