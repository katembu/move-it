#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
# maintainer: henrycg


class Indicator(object):
    _agg_func = None
    _for_week = None
    _print_func = None
    title = None

    def __unicode__(self):
        return u"\"<Indicator: %s (excel: %s)>\"" % (self.title, self._excel)

    def __str__(self):
        return str(self.__unicode__())

    @classmethod
    def PERC_PRINT(cls, (num, den), excel):
        if den == 0: return '--'
   
        frac = float(num)/float(den)
        if excel:
            return frac
        
        return "%2.1f%% (%d/%d)" % (100.0*frac, num, den)
    
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

    def __init__(self, title, for_week, row_agg_func, \
            print_func=None, col_agg_func=None, excel=True):

        self.title = title
        self._excel = excel
        self._row_agg_func = row_agg_func
        self._for_week = for_week

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

    def _for_month(self):
        return self._row_agg_func([self._for_week(w) for w in xrange(0,4)])

    def for_month(self):
        return self._print_func(self._for_month(), self._excel)
    def for_month_raw(self):
        return self._for_month()

    def for_week(self, week_num):
        return self._print_func(self._for_week(week_num), self._excel)
    def for_week_raw(self, week_num):
        return self._for_week(week_num)

    def aggregate_col(self, lst):
        return self._print_func(\
            self._col_agg_func(lst), self._excel)

    @property
    def is_percentage(self):
        return self._print_func == Indicator.PERC_PRINT

    @classmethod
    def empty_func(self, week_num):
        return ''


INDICATOR_EMPTY = Indicator('________', \
    Indicator.empty_func, \
    Indicator.empty_func)
