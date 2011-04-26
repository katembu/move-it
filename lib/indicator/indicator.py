#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import numbers

from django.db.models.query import QuerySet
from django.utils.translation import ugettext as _

class QuerySetType(object):
    mtype = None
    def __init__(self, mtype):
        self.mtype = mtype

class Indicator(object):
    type_in     = None
    type_out    = None

    slug        = None
    short_name  = None
    long_name   = None

    valid_for   = None

    output_is_number = issubclass(type_output, numbers.Number)

    @classmethod
    def _check_type(cls, expected, value, s):
        if expected is QuerySet:
            raise TypeError(_("Expected %(str)s type cannot be a QuerySet. "\
                            "Use an indicator.QuerySetType object instead.") % \
                            {'str': s)

        # First, check if we're dealing with a QuerySetType object
        if isinstance(expected, QuerySetType):
            if not isinstance(value, QuerySet):
                raise TypeError(_("Expected %(str)s type %(exp)s but got illegal " \
                                    "%(str)s type %(ill)s!") % \
                                    {'exp': QuerySet, 'ill': type(data_in), 'str': s})

            if value.model is not expected.mtype:
                raise TypeError(_("Expected %(str)s QuerySet type %(exp)s but got illegal " \
                                    "%(str)s QuerySet type %(ill)s!") % \
                                    {'exp': expected.mtype, 'ill': value.model, 'str': s})

        # If we don't have a QuerySetType, then just do regular type checking
        else:
            if not isinstance(value, expected):
                raise TypeError(_("Expected %(str)s type %(exp)s but got illegal " \
                                    "%(str)s type %(ill)s!") % \
                                    {'exp': cls.type_in, 'ill': type(data_in), 'str': s})


    @classmethod
    def value(cls, period, data_in):
        cls._check_type(type_in, data_in, _("input"))
        data_out = cls._value(period, in_data)
        cls._check_type(type_out, data_out, _("output"))
        return out_data

