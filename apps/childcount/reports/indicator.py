#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

"""
Indicator class: Used for tracking value of a
function over time period.
"""
class Indicator(object):
    _agg_func = None
    _for_period = None
    _print_func = None
    title = None

    def __unicode__(self):
        return u"\"<Indicator: %s (excel: %s)>\"" % (self.title, self._excel)

    def __str__(self):
        return str(self.__unicode__())

    """ Print function for percentages.  We 
        store percentages internally as 
        (numerator, denominator) pairs so
        that we can later average the
        percentage values.
    """
    @classmethod
    def PERC_PRINT(cls, (num, den), excel):
        if den == 0: return '--'
   
        frac = float(num)/float(den)
        if excel:
            return frac
        
        return "%2.1f%% (%d/%d)" % (100.0*frac, num, den)
   
    @classmethod
    def PERC_PRINT_SHORT(cls, (num, den), excel):
        if den == 0: return '--'
   
        frac = float(num)/float(den)
        if excel:
            return frac
        
        return "%d%%" % int(round(100.0*frac))

    """ Default print function.  Tries to 
        convert to int or float for the benefit
        of doing Excel calculations, then 
        reverts to a string.
    """
    @classmethod
    def print_func_default(cls, val, excel):
        out = None

        if val is None:
            return u"--"

        try:
            out = int(val)
        except ValueError:
            pass

        if out is None:
            try:
                out = float(val)
            except ValueError:
                pass

        if out is None:
            print "string: %s" % val
            out = unicode(val)
        return out


    ''' Aggregation functions
        (for giving a total/average at the end of a row)
    '''
    @classmethod
    def AGG_PERCS(cls, lst):
        # We get a lst of (numerator, denominator) tuples
        # Separate the numerators and denominators
        if len(lst) == 0:
            return (0,0)
        
        print lst
        (nums, dens) = zip(*lst)
        print (nums, dens)
        return (sum(nums), sum(dens))
 
    @classmethod
    def AVG(cls, lst, roundoff=False):
        lst = filter(lambda a: a is not None, lst)
        if len(lst) == 0:
            return None
        if roundoff:
            return int(sum(lst, 0.0) / len(lst))
        return sum(lst, 0.0) / len(lst)

    @classmethod
    def SUM(cls, lst):
        lst = filter(lambda a: a is not None, lst)
        return sum(lst) 

    def __init__(self, title, for_period, row_agg_func, \
            print_func=None, col_agg_func=None, excel=True):

        # Report title
        self.title = title
        
        # True if this is for excel export
        self._excel = excel

        # Function to aggregate across time periods
        # e.g., to add list of week values to get
        # the monthly total
        self._row_agg_func = row_agg_func

        # Function called with a period class and
        # period number that returns the value of
        # this indicator
        self._for_period = for_period

        if print_func is None:
            self._print_func = self.print_func_default
        else:
            self._print_func = print_func

        if col_agg_func is None:
            self._col_agg_func = row_agg_func
        else:
            self._col_agg_func = col_agg_func

    def set_excel(self, val):
        if val not in [False, True]:
            raise ValueError('Excel value must be a boolean')
        self._excel = val

    def _for_total(self, per_cls):
        return self._row_agg_func([\
            self.for_period_raw(per_cls, per_num) \
                for per_num in xrange(0, per_cls.num_periods)])

    """ Total for a set of time periods """
    def for_total(self, per_cls):
        return self._print_func(self._for_total(per_cls), self._excel)

    def for_total_raw(self, per_cls):
        return self._for_total(per_cls)

    """ Indicator value for a single period """
    def for_period(self, per_cls, per_num):
        return self._print_func(\
            self._for_period(per_cls, per_num), self._excel)

    def for_period_raw(self, per_cls, per_num):
        return self._for_period(per_cls, per_num)

    """ Column aggregate value (e.g., for summing
    HH visits for all CHWs in a time period) """
    def aggregate_col(self, lst):
        return self._print_func(\
            self._col_agg_func(lst), self._excel)

    @property
    def is_percentage(self):
        return self._print_func in \
            (Indicator.PERC_PRINT, Indicator.PERC_PRINT_SHORT)

    @property
    def is_full_percentage(self):
        return self._print_func == Indicator.PERC_PRINT

    @classmethod
    def empty_func(self, *vargs):
        return ''


""" Using for separating groups of indicator values """
INDICATOR_EMPTY = Indicator('________', \
    Indicator.empty_func, \
    Indicator.empty_func)
