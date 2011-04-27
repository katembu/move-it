#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import numbers

from percentage import Percentage

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

    @classmethod
    def _value(cls, period, data_in):
        raise NotImplementedError(_("No value method implemented!"))

    
    '''
    You shouldn't have implement anything below this line
    in your Indicator subclasses...
    '''

    @classmethod
    def output_is_number(cls):
        return issubclass(type_out, numbers.Number)

    @classmethod
    def _check_type(cls, expected, value, s):
        if expected is QuerySet:
            raise TypeError(_("Expected %(str)s type cannot be a QuerySet. "\
                            "Use an indicator.QuerySetType object instead.") % \
                            {'str': s})

        # First, check if we're dealing with a QuerySetType object
        if isinstance(expected, QuerySetType):
            if not isinstance(value, QuerySet):
                raise TypeError(_("Expected %(str)s type %(exp)s but got illegal " \
                                    "%(str)s type %(ill)s!") % \
                                    {'exp': QuerySet, 'ill': type(value), 'str': s})

            if value.model is not expected.mtype:
                raise TypeError(_("Expected %(str)s QuerySet of type %(exp)s but got illegal " \
                                    "%(str)s QuerySet of type %(ill)s!") % \
                                    {'exp': expected.mtype, 'ill': value.model, 'str': s})

        # If we don't have a QuerySetType, then just do regular type checking
        else:
            if not isinstance(value, expected):
                raise TypeError(_("Expected %(str)s type %(exp)s but got illegal " \
                                    "%(str)s type %(ill)s!") % \
                                    {'exp': expected, 'ill': type(value), 'str': s})


    def __new__(cls, period, data_in):
        cls._check_type(cls.type_in, data_in, _("input"))
        data_out = cls._value(period, data_in)
        cls._check_type(cls.type_out, data_out, _("output"))
        return data_out 

class PercentageIndicator(Indicator):
    cls_num = None
    cls_den = None

    type_out = Percentage

    @classmethod
    def _value(cls, period, data_in):
        return Percentage(cls_num(period, data_in), cls_den(period, data_in))

class DifferenceIndicator(Indicator):
    cls_first   = None
    cls_second  = None

    @classmethod
    def _value(cls, period, data_in):
        if cls.cls_first.type_out != cls.cls_second.type_out:
            raise TypeError(_("Cannot compute difference of indicators "\
                                "with unequal types!"))

        return (cls.cls_first(period, data_in) - cls.cls_second(period, data_in))


