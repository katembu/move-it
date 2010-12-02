#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg

def print_func(val, excel):
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

class Indicator(object):
    _agg_func = None
    _for_week = None
    _print_func = None
    title = None

    EMPTY_FUNC = lambda n: ''
    EMPTY = ('________', EMPTY_FUNC, EMPTY_FUNC) 

    @classmethod
    def PERC_PRINT(cls, (num, den), excel):
        if den == 0: return '--'
   
        frac = float(num)/float(den)
        if excel:
            return frac
        
        return "%2.1f%% (%d/%d)" % (100.0*frac, num, den)

    @classmethod
    def AGG_PERCS(cls, lst):
        # We get a lst of (numerator, denominator) tuples
        # Separate the numerators and denominators
        if len(lst) == 0:
            return (0,0)

        (nums, dens) = zip(*lst)
        return (sum(nums), sum(dens))
 
    ''' Aggregation functions
        (for giving a total/average at the end of a row)
    '''
    @classmethod
    def AVG(cls, lst):
        lst = filter(lambda a: a is not None, lst)
        if len(lst) == 0:
            return None
        return sum(lst, 0.0) / len(lst)

    @classmethod
    def SUM(cls, lst):
        lst = filter(lambda a: a is not None, lst)
        return sum(lst) 

    def __init__(self, title, for_week, agg_func, \
            print_func=print_func, excel=True):
        self.title = title
        self._excel = excel
        self._agg_func = agg_func
        self._for_week = for_week
        self._print_func = print_func

    def _for_month(self):
        return self._agg_func([self._for_week(w) for w in xrange(0,4)])

    def for_month(self):
        return self._print_func(self._for_month(), self._excel)
    def for_month_raw(self):
        return self._for_month()

    def for_week(self, week_num):
        return self._print_func(self._for_week(week_num), self._excel)
    def for_week_raw(self, week_num):
        return self._for_week(week_num)

    def aggregate(self, lst):
        return self._print_func(self._agg_func(lst), self._excel)

    @property
    def is_percentage(self):
        return self._print_func == Indicator.PERC_PRINT

