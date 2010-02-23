#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: dgelvin

from django.utils.translation import ugettext as _


class InvalidAge(Exception):
    pass


class InvalidDOB(Exception):
    pass


class AmbiguousAge(Exception):
    pass


class ParseError(Exception):

    def __init__(self, message=_(u"FAILED. unable to understand")):
        self.message = message


class BadValue(Exception):

    def __init__(self, message=_(u"FAILED. Bad value")):
        self.message = message


class Inapplicable(Exception):

    def __init__(self, message=_(u"FAILED. Not applicable")):
        self.message = message
