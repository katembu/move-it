#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import numbers

from percentage import Percentage
from cache import cache_indicator
from query_set_type import QuerySetType

from django.db.models.query import QuerySet
from django.utils.translation import ugettext as _

class Indicator(object):
    type_in     = None
    type_out    = None

    slug        = None
    short_name  = None
    long_name   = None

    cache       = True
    # Default to two hours
    valid_for   = 2*60*60

    @classmethod
    def _value(cls, period, data_in):
        raise NotImplementedError(_("No value method implemented!"))

    
    '''
    You shouldn't have implement anything below this line
    in your Indicator subclasses...
    '''

    @classmethod
    def input_is_query_set(cls):
        return isinstance(cls.type_in, QuerySetType)

    @classmethod
    def output_is_number(cls):
        return issubclass(cls.type_out, numbers.Number)

    @classmethod
    def output_is_percentage(cls):
        return issubclass(cls.type_out, Percentage)

    @classmethod
    def _check_type(cls, expected, value, s):
        if cls.slug is None:
            raise ValueError(_("Indicator slug cannot be None"))

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
        data_out = cache_indicator(cls, cls._value, period, data_in)
        cls._check_type(cls.type_out, data_out, _("output"))
        return data_out 

class IndicatorPercentage(Indicator):
    cls_num = None
    cls_den = None

    type_out = Percentage

    @classmethod
    def _value(cls, period, data_in):
        return Percentage(cls.cls_num(period, data_in), cls.cls_den(period, data_in))

class IndicatorDifference(Indicator):
    cls_first   = None
    cls_second  = None

    @classmethod
    def _value(cls, period, data_in):
        if cls.cls_first.type_out != cls.cls_second.type_out:
            raise TypeError(_("Cannot compute difference of indicators "\
                                "with unequal types!"))

        return (cls.cls_first(period, data_in) - cls.cls_second(period, data_in))


